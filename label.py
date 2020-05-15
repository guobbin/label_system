#encoding: utf-8

from flask import Flask, render_template, request, redirect, url_for, session, make_response, send_file
import config
from exts import db
from models import User, Access, UltraImage, UltraReport, Pathology
from decorator import login_required
from page_utils import Pagination
import  os
import pandas as pd
from datetime import datetime
import time
import sqlalchemy
import pytesseract
from PIL import Image

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)


@app.route('/upload/', methods=['POST', 'GET'])
@login_required
def upload():
    if request.method == 'POST':
        basepath = os.path.dirname(__file__)  # 当前文件所在路径
        relative_path = os.path.join('static', 'uploads')  # 注意：没有的文件夹一定要先创建，不然会提示没有该路径
        upload_path = os.path.join(basepath, relative_path)  # upload的目录
        upload_key = str(int(time.time()))  # 时间戳为每次上传的文件加以区分
        target = os.path.join(upload_path, upload_key)
        os.mkdir(target)  # 创建文件夹
        date_set_path = ''
        date_set_name = ''
        files = request.files.getlist('file')
        for file1 in files:  # 对上传的每个文件进行分析得到上传文件夹的目录结果
            namelist = file1.filename.split('/')
            date_set_name = namelist[0]  # data_set文件名
            date_set_path = os.path.join(target, date_set_name)
            if not os.path.exists(date_set_path):  # 只需创建一次
                os.mkdir(date_set_path)
            patient_access_path = os.path.join(date_set_path, namelist[1])  # access文件名
            if not os.path.exists(patient_access_path):  # 只需创建一次
                os.mkdir(patient_access_path)
            patientID = namelist[1].split('_')[0]   # patientID文件名
            accessID = namelist[1].split('_')[1]    # accessID文件名
            patientID_path = os.path.join(patient_access_path, patientID)
            accessID_path = os.path.join(patient_access_path, accessID)
            if not os.path.exists(patientID_path):  # 只创建一次
                os.mkdir(patientID_path)
                os.mkdir(accessID_path)
            fp = os.path.join(target, file1.filename)
            # if fp.split('.')[1] == 'txt':
            #   #  fo = open(file1)
            #     ultra_report = ''
            #     for row in open(file1).readlines():
            #         ultra_report += row.decode('gbk').encode('utf8')
            #    # ultra_report = unicode(ultra_report, 'utf-8')
            #     write_file = open(fp.split('.')[0]+'1.txt', 'w')
            #     write_file.write(ultra_report)
            #     write_file.close()
            file1.save(fp)  # 保存每个文件
        file_path = date_set_path
        file_list = os.listdir(file_path)
        parent = 'uploads/'+upload_key+'/'+date_set_name

        for file_name in file_list:    # 对每个access文件

            patient_access = file_name.split('_')  # 由命名规则分解出patient_id和access_id
            patient_id = patient_access[0]
            access_id = patient_access[1]

            access_path = parent+'/' + file_name  # 合成文件路径
            user_id = session.get('user_id')  # 获取上传者id
            access = Access(filename=file_name, file_path=access_path, PatientID=patient_id, ACCESSID=access_id,
                            uploader_id=user_id, upload_time=datetime.now())
            db.session.add(access)
            db.session.commit()  # 添加access

            ultra_report_name = file_name + '.txt'  # 合成超声报告文件名
            ultra_report_path = access_path+'/'+ultra_report_name   # 合成超声报告文件目录
            ultra_report = UltraReport(file_path=ultra_report_path, filename=ultra_report_name, access_id=access.id)
            db.session.add(ultra_report)    # 添加ultra_report到数据库

            file_path1 = os.path.join(file_path, file_name, access_id)  # 合成存放超声图片的文件夹路径
            file_list1 = os.listdir(file_path1)     # 获取所有超声图片文件名
            for file_name1 in file_list1:    # 对每张超声图片
                ultra_image_name = file_name1   # 文件名赋值
                ultra_image_path = access_path + '/' + access_id + '/' +file_name1  # 文件路径合成
                ultra_image = UltraImage(file_path=ultra_image_path,
                                         filename=ultra_image_name, access_id=access.id)    # 生成超声图片对象
                db.session.add(ultra_image)     # 添加超声图片
            access.has_pathology = False    # 默认设置为无病理报告
            file_path2 = os.path.join(file_path, file_name, patient_id)  # 合成存放病理报告的文件夹路径
            file_list2 = os.listdir(file_path2)     # 获取所有病理报告文件名
            if file_list2:   # 存在存放病理报告的文件夹
                access.has_pathology = True      # 该access有病理报告
                for file_name2 in file_list2:   # 对每个病理报告
                    pathology_name = file_name2 # 文件名赋值
                    pathology_path = access_path + '/' + patient_id + '/' +file_name2   # 文件路径合成
                    pathology = Pathology(file_path=pathology_path,
                                          filename=pathology_name, access_id=access.id)     # 生成病理报告对象
                    db.session.add(pathology)   # 提交添加
            db.session.commit()     # 提交access有无病理报告的修改
        return redirect(url_for('index'))
    return render_template('upload.html')


@app.route('/')
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    per_page = 5

    count = Access.query.count()
    pager_obj = Pagination(page, count, request.path, request.args, per_page_count=per_page)
    accesses = Access.query.order_by('-id').paginate(page, per_page, error_out=False).items

    html = pager_obj.page_html()
    return render_template("index.html", accesses=accesses, html=html, is_progress=False)


@app.route('/progress/<user_id>')
@login_required
def progress(user_id):
    page = request.args.get("page", 1, type=int)
    per_page = 5
    is_admin = True

    if user_id == '0':
        user_id = session.get('user_id')
        not_admin = False

    count = Access.query.filter(Access.labeler_id == user_id).count()
    pager_obj = Pagination(page, count, request.path, request.args, per_page_count=per_page)
    accesses = Access.query.filter(Access.labeler_id == user_id).order_by('-id').paginate(page, per_page,
                                                                                          error_out=False).items
    html = pager_obj.page_html()
    return render_template('index.html', accesses=accesses, html=html, is_progress=True, is_admin=is_admin)


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        username = request.form.get('username') #表单获取的用户名
        password = request.form.get('password') #表单获取的用户密码
        user = User.query.filter(User.username == username, User.password == password).first() #根据用户名和密码查询用户
        if user: #用户存在则跳转登录
            session['user_id'] = user.id
            session.permanent = True
            return redirect(url_for('index'))
        else: #登录失败
            return u'用户名或者密码错误'


@app.route('/export/', methods=['GET', 'POST'])
@login_required
def export():
    if request.method == 'GET':
        return render_template('export.html')
    else:
        query = UltraImage.query   # 查询超声图片表
        if request.form.get('time1'):
            dt1 = datetime.strptime(request.form.get('time1'), '%Y-%m-%d %H:%M')
            query = query.filter(UltraImage.create_time >= dt1)  # 限制不早于
        if request.form.get('time2'):
            dt2 = datetime.strptime(request.form.get('time2'), '%Y-%m-%d %H:%M')
            query = query.filter(UltraImage.create_time <= dt2)  # 限制不晚于
        if request.form.get('labeled'):
            query = query.join(Access).filter(Access.labeled)   # 限制已标注
        image_list = query.all()  # 查询结果
        if not image_list:  # 若结果为空则重新跳导入界面
            return render_template('export.html')
        IDs = []
        accs = []
        flns = []
        labels = []
        pats = []
        regs = []
        bors = []
        blos = []
        pars = []
        sins = []
        slas = []
        dess = []
        cons = []
        xs = []
        ys = []
        wids = []
        heis = []
        for image in image_list:
            IDs.append(image.access.PatientID)
            accs.append(image.access.ACCESSID)
            flns.append(image.filename)
            labels.append(image.access.result)
            pats.append([u'是', u'否'][image.access.has_pathology])
            regs.append(image.regulation)
            bors.append(image.border)
            blos.append(image.bloodstream)
            pars.append(image.part)
            sins.append(image.single_training)
            slas.append(image.single_label)
            dess.append(image.desc)
            cons.append(image.conclusion)
            xs.append(image.x)
            ys.append(image.y)
            wids.append(image.width)
            heis.append(image.height)
        dict1 = {'a-ID': IDs, 'b1-acc': accs,'b2-fln': flns, 'c-pat': pats, 'd-lab': labels, 'e-reg': regs,
                 'f-bor': bors, 'g-blo': blos, 'h-par': pars, 'i-sin': sins, 'j-sla': slas, 'k-des': dess,
                 'l-con': cons}
        dict2 = {'a-ID': 'ID', 'b1-acc': 'ACCESSID', 'b2-fln': u'图片名', 'c-pat': u'有病理报告', 'd-lab': u'标注',
                 'e-reg': u'形状', 'f-bor': u'边界', 'g-blo': u'血流', 'h-par': u'部位', 'i-sin':u'可用于单张训练',
                 'j-sla': u'单张分级', 'k-des': u'回声描述', 'l-con': u'结论'}
        dict3 = {}
        cols = []
        namelist = []
        for name in request.form:
            namelist.append(name)
        namelist.sort()
        for name in namelist:
              if len(name.split('-')) > 1:
                dict3[dict2[name]] = dict1[name]
                cols.append(dict2[name])
        if request.form.get('scr'):
            dict3[u'起点x'] = xs
            dict3[u'起点y'] = ys
            dict3[u'长度'] = wids
            dict3[u'宽度'] = heis
            cols.append(u'起点x')
            cols.append(u'起点y')
            cols.append(u'长度')
            cols.append(u'宽度')

        ress = pd.DataFrame(dict3)  # dict3为整理好的导出数据
        ress = ress.ix[:, cols]
        times = str(int(time.time()))  # 时间戳作为文件名
        basepath = os.path.dirname(__file__)
        store_path = os.path.join(basepath, 'static', 'download', times+'.xls')
        ress.to_excel(store_path)
        response = make_response(send_file(store_path))
        response.headers["Content-Disposition"] = "attachment; filename="+times+".xls;"
        return response  # 导出数据供用户下载


@app.route('/logout/')
@login_required
def logout():
    # session.pop('user_id')
    # del session['user_id']
    session.clear()
    return redirect(url_for('login'))


@app.route('/detail/<access_id>', methods=['POST', 'GET'])
@login_required
def detail(access_id):
    access = Access.query.filter(Access.id == access_id).first()    # 根据access_id查询access
    ultra_report = ''
    ultra_report_path = os.path.dirname(__file__) + './static/' + access.ultra_report[0].file_path
    for row in open(ultra_report_path).readlines():
        ultra_report += row.decode('gbk').encode('utf8')
    ultra_report = unicode(ultra_report, 'utf-8')

    access1 = Access.query.filter(Access.id > access_id).first()    # 顺序查询找到上一例
    access2 = Access.query.order_by('-id').filter(Access.id < access_id).first()    # 根据id倒查询找到下一例
    next_access_id = last_access_id = access_id   # 初始化为当前页
    if access2:  # 若存在则赋值，若与access_id 相等则为空
        next_access_id = access2.id
    if access1:
        last_access_id = access1.id

    images = UltraImage.query.order_by('filename').filter(UltraImage.access_id == access_id).all()
    if request.method == 'POST':  # POST方式
        for image in access.ultra_images:   # 对每张超声图片
            image.regulation = request.form.get('regulation'+image.filename)  # 形状
            image.border = request.form.get('border'+image.filename)  # 边界
            image.bloodstream = request.form.get('bloodstream'+image.filename)  # 血流
            image.part = request.form.get('part'+image.filename)  # 部位
            image.single_training = request.form.get('single_training'+image.filename)  # 单张训练
            image.single_label = request.form.get('single_label'+image.filename)  # 单张标注
            image.desc = request.form.get('desc'+image.filename)  # 超声描述
            image.conclusion = request.form.get('conclusion'+image.filename)  # 结论
            aixs = request.form.get('axis'+image.filename).split(',')  # 截框坐标
            image.x = aixs[0]
            image.y = aixs[1]
            image.width = aixs[2]
            image.height = aixs[3]
        access.result = request.form.get('result')  # 修改标记
        access.labeled = True   # 修改是否标注
        access.label_time = datetime.now()   # 修改标记时间
        access.labeler_id = session.get('user_id')   # 记录标注人
        db.session.commit()     # 提交修改

    return render_template('detail.html', access=access, ultra_report=ultra_report,
                           next_access_id=next_access_id, last_access_id=last_access_id, images=images)


@app.route('/add_user/', methods=['POST', 'GET'])
@login_required
def add_user():
    if request.method == 'GET':
        return render_template('add_user.html')
    else:
        username = request.form.get('username')
        select = request.form.get('is_admin')
        if select == u'是':
            is_admin = True
        elif select == u'否':
            is_admin = False
        else:
            return u'请先选择该用户权限'
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter(User.username == username).first()

        if user:
            return u'该用户名被注册'
        else:
            if password1 != password2:
                return u"请确保两次密码一致"
            else:
                user = User(username=username, is_admin=is_admin, password=password1)
                db.session.add(user)
                db.session.commit()
                return redirect(url_for('login'))


@app.route('/progress_admin/')
@login_required
def progress_admin():
    page = request.args.get("page", 0, type=int)
    per_page = 8

    count = User.query.count()
    pager_obj = Pagination(page, count, request.path, request.args, per_page_count=per_page)
    # accesses = Access.qu  ery.order_by('-id').paginate(page, per_page, error_out=False).items
    # user = User.query.order_by().

    access_sub = Access.query.group_by(Access.labeler_id).with_entities(Access.labeler_id, sqlalchemy.func.count(
        Access.labeler_id).label('count')).subquery()
    result = db.session.query(User, access_sub.c.count).join(access_sub, User.id == access_sub.c.labeler_id).order_by(
        access_sub.c.count.desc()).paginate(page, per_page, error_out=False).items

    print(request.path)
    print(request.args)
    # index_list = li[pager_obj.start:pager_obj.end]
    html = pager_obj.page_html()
    return render_template('progress_admin.html', result=result, html=html)


@app.route('/help/')
def help():
    return render_template('help.html')


@app.context_processor
def my_context_processor():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.filter(User.id == user_id).first()
        if user:
            return {'user': user}
    return {}


if __name__ == '__main__':
    app.run()
