import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__="users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    hash = db.Column(db.String, nullable=False)
    cash = db.Column(db.Float, nullable=False)
    def __init__(self, username, hash, cash):
        self.username = username
        self.hash = hash
        self.cash = cash
    """summ = db.relationship("Summ", backref="user", lazy=True)

    def add_summ(self, symbol, price, shares, total):
        summ = Summ(userId=self.id, symbol=symbol, price =price, shares=shares, total=total)
        db.session.add(summ)
        db.session.commit()"""

#symbol, price, shares, total
class Summ(db.Model):
    __tablename__="summ"
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, nullable=False)
    symbol = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    shares = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Float, nullable=False)
    def __init__(self, userId, symbol, price, shares, total):
        self.userId = userId
        self.symbol = symbol
        self.price = price
        self.shares = shares
        self.total = total

#userId, symbol, shares, price, time
class Portfolio(db.Model):
    __tablename__="portfolio"
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, nullable=False)
    symbol = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    shares = db.Column(db.Integer, nullable=False)
    time = db.Column(db.DateTime, nullable=False)
