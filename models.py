#encoding:utf-8
from exts import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(100), nullable=False)

    # labeled_accesses = db.relationship('Access', backref='labeler', lazy='dynamic')


class Access(db.Model):
    __tablename__ = 'access'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ACCESSID = db.Column(db.String(50), nullable=False)
    PatientID = db.Column(db.String(50), nullable=False)
    filename = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.Text, nullable=False)
    labeled = db.Column(db.Boolean, nullable=False, default=False)
    label_time = db.Column(db.Date, default=datetime.now)
    has_pathology = db.Column(db.Boolean, default=False)
    result = db.Column(db.String(50), default=u'-分级-')
    upload_time = db.Column(db.Date, default=datetime.now)

    labeler_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    labeler = db.relationship('User', backref=db.backref('label_accesses'), foreign_keys=[labeler_id])

    uploader = db.relationship('User', backref=db.backref('upload_accesses'), foreign_keys=[uploader_id])

    # ultra_images = db.relationship('UltraImage', back_populates='access')


class UltraImage(db.Model):
    __tablename__ = 'ultra_image'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.Text, nullable=False)

    regulation = db.Column(db.String(50), default=u'-形状-')
    border = db.Column(db.String(50), default=u'-边界-')
    bloodstream = db.Column(db.String(50),  default=u'-血流-')
    part = db.Column(db.String(50), default=u'-部位-')
    single_training = db.Column(db.String(50), default=u'-单张训练-')
    single_label = db.Column(db.String(50), default=u'-单张分级-')
    desc = db.Column(db.Text, default='')
    conclusion = db.Column(db.Text, default='')
    x = db.Column(db.String(50), default=u'77')
    y = db.Column(db.String(50), default=u'58')
    width = db.Column(db.String(50), default=u'614')
    height = db.Column(db.String(50), default=u'461')
    create_time = db.Column(db.DateTime, default=datetime.now)

    access_id = db.Column(db.Integer, db.ForeignKey('access.id'))
    access = db.relationship('Access', backref=db.backref('ultra_images'))


class Pathology(db.Model):
    __tablename__ = 'pathology'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.Text, nullable=False)

    access_id = db.Column(db.Integer, db.ForeignKey('access.id'))
    access = db.relationship('Access', backref=db.backref('pathologies'))


class UltraReport(db.Model):
    __tablename__ = 'ultra_report'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.Text, nullable=False)

    access_id = db.Column(db.Integer, db.ForeignKey('access.id'))
    access = db.relationship('Access', backref=db.backref('ultra_report'), uselist=False)
