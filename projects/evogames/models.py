##################################################################
# models.py
#
# This file contains the models for the application.
#
# @author: Theodore Mui
# @version: 1.0
# @since: 2025-05-03
#
##################################################################

from datetime import datetime
from app import db

class Configuration(db.Model):
    """Model for storing simulation configurations"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    game_type = db.Column(db.String(50), nullable=False)
    config_data = db.Column(db.Text, nullable=False)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Configuration {self.name}>"

class SimulationResult(db.Model):
    """Model for storing simulation results"""
    id = db.Column(db.Integer, primary_key=True)
    configuration_id = db.Column(db.Integer, db.ForeignKey('configuration.id'), nullable=False)
    result_data = db.Column(db.Text, nullable=False)  # JSON string
    stats_summary = db.Column(db.Text, nullable=True)  # JSON string for summary statistics
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    configuration = db.relationship('Configuration', backref=db.backref('results', lazy=True))

    def __repr__(self):
        return f"<SimulationResult {self.id} for config {self.configuration_id}>"
