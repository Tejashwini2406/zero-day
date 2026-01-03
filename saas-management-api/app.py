#!/usr/bin/env python3
"""
Zero-Day SaaS Management API
Tenant management, billing, usage metering, and subscription management
"""

from flask import Flask, request, jsonify
from functools import wraps
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import jwt
import os
import subprocess
import json
import sqlite3
import uuid
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'CHANGE_ME_IN_PRODUCTION')

# Database initialization
DB_PATH = '/data/saas-management.db'

class BillingTier(Enum):
    """Subscription tiers"""
    FREE = {
        'rps_limit': 10,
        'concurrent_limit': 5,
        'storage_gb': 10,
        'price_monthly': 0,
        'features': ['basic_detection']
    }
    STARTER = {
        'rps_limit': 100,
        'concurrent_limit': 20,
        'storage_gb': 100,
        'price_monthly': 99,
        'features': ['basic_detection', 'api_access']
    }
    PROFESSIONAL = {
        'rps_limit': 500,
        'concurrent_limit': 100,
        'storage_gb': 500,
        'price_monthly': 499,
        'features': ['basic_detection', 'api_access', 'custom_rules', 'advanced_analytics']
    }
    ENTERPRISE = {
        'rps_limit': 2000,
        'concurrent_limit': 500,
        'storage_gb': 5000,
        'price_monthly': 2000,
        'features': ['all', 'sso', 'dedicated_support', 'sla']
    }

def init_db():
    """Initialize SQLite database for SaaS management"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Tenants table
    c.execute('''
        CREATE TABLE IF NOT EXISTS tenants (
            tenant_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            billing_tier TEXT NOT NULL,
            namespace TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active',
            api_key TEXT UNIQUE NOT NULL,
            custom_domain TEXT
        )
    ''')
    
    # Usage tracking table
    c.execute('''
        CREATE TABLE IF NOT EXISTS usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            date DATE DEFAULT CURRENT_DATE,
            requests_count INTEGER DEFAULT 0,
            inference_calls INTEGER DEFAULT 0,
            storage_gb_used REAL DEFAULT 0,
            FOREIGN KEY(tenant_id) REFERENCES tenants(tenant_id)
        )
    ''')
    
    # Invoices table
    c.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            amount_cents INTEGER NOT NULL,
            status TEXT DEFAULT 'draft',
            issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due_date DATE,
            paid_at TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(tenant_id)
        )
    ''')
    
    # Subscription events
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscription_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            old_tier TEXT,
            new_tier TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(tenant_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def require_auth(f):
    """Authentication decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Missing authentication token'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            request.tenant_id = data['tenant_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    """Admin authentication decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key', '')
        if not api_key or api_key != os.getenv('ADMIN_API_KEY', 'CHANGE_ME'):
            return jsonify({'error': 'Invalid admin credentials'}), 401
        return f(*args, **kwargs)
    return decorated

# API Endpoints

@app.route('/api/v1/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/v1/auth/register', methods=['POST'])
def register_tenant():
    """Register new tenant"""
    data = request.json
    required_fields = ['name', 'email', 'billing_tier']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if data['billing_tier'] not in [tier.name.lower() for tier in BillingTier]:
        return jsonify({'error': 'Invalid billing tier'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        tenant_id = f"tenant-{uuid.uuid4().hex[:12]}"
        api_key = f"key-{uuid.uuid4().hex[::2]}"
        namespace = f"tenant-{tenant_id}"
        
        c.execute('''
            INSERT INTO tenants (tenant_id, name, email, billing_tier, namespace, api_key)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (tenant_id, data['name'], data['email'], data['billing_tier'].upper(), namespace, api_key))
        
        conn.commit()
        
        # Create tenant namespace in Kubernetes
        create_tenant_namespace(tenant_id, data['name'], data['billing_tier'])
        
        # Generate JWT token
        token = jwt.encode({
            'tenant_id': tenant_id,
            'email': data['email'],
            'exp': datetime.utcnow() + timedelta(days=365)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'tenant_id': tenant_id,
            'api_key': api_key,
            'token': token,
            'namespace': namespace
        }), 201
    
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Tenant already exists'}), 409
    finally:
        conn.close()

@app.route('/api/v1/tenants/<tenant_id>', methods=['GET'])
@require_auth
def get_tenant(tenant_id):
    """Get tenant information"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT tenant_id, name, email, billing_tier, namespace, created_at, status
        FROM tenants WHERE tenant_id = ?
    ''', (tenant_id,))
    
    row = c.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'error': 'Tenant not found'}), 404
    
    return jsonify({
        'tenant_id': row[0],
        'name': row[1],
        'email': row[2],
        'billing_tier': row[3],
        'namespace': row[4],
        'created_at': row[5],
        'status': row[6]
    })

@app.route('/api/v1/tenants/<tenant_id>/usage', methods=['GET'])
@require_auth
def get_tenant_usage(tenant_id):
    """Get tenant usage metrics"""
    days = request.args.get('days', 30, type=int)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    c.execute('''
        SELECT date, requests_count, inference_calls, storage_gb_used
        FROM usage
        WHERE tenant_id = ? AND date >= ?
        ORDER BY date DESC
    ''', (tenant_id, start_date.date()))
    
    rows = c.fetchall()
    conn.close()
    
    total_requests = sum(row[1] for row in rows)
    total_inferences = sum(row[2] for row in rows)
    max_storage = max((row[3] for row in rows), default=0)
    
    return jsonify({
        'tenant_id': tenant_id,
        'period_days': days,
        'total_requests': total_requests,
        'total_inferences': total_inferences,
        'max_storage_gb': max_storage,
        'daily_usage': [
            {
                'date': row[0],
                'requests': row[1],
                'inferences': row[2],
                'storage_gb': row[3]
            } for row in rows
        ]
    })

@app.route('/api/v1/tenants/<tenant_id>/upgrade', methods=['POST'])
@require_auth
def upgrade_tenant(tenant_id):
    """Upgrade tenant billing tier"""
    data = request.json
    new_tier = data.get('billing_tier', '').upper()
    
    if new_tier not in [tier.name for tier in BillingTier]:
        return jsonify({'error': 'Invalid billing tier'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get current tier
    c.execute('SELECT billing_tier FROM tenants WHERE tenant_id = ?', (tenant_id,))
    current_tier = c.fetchone()[0]
    
    # Update tier
    c.execute('''
        UPDATE tenants SET billing_tier = ? WHERE tenant_id = ?
    ''', (new_tier, tenant_id))
    
    # Log subscription event
    c.execute('''
        INSERT INTO subscription_events (tenant_id, event_type, old_tier, new_tier)
        VALUES (?, 'upgrade', ?, ?)
    ''', (tenant_id, current_tier, new_tier))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Tenant {tenant_id} upgraded from {current_tier} to {new_tier}")
    
    return jsonify({
        'message': f'Upgraded to {new_tier}',
        'previous_tier': current_tier,
        'new_tier': new_tier
    })

@app.route('/api/v1/billing/invoices', methods=['GET'])
@require_auth
def list_invoices():
    """List invoices for tenant"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT invoice_id, amount_cents, status, issued_at, due_date, paid_at
        FROM invoices
        WHERE tenant_id = ?
        ORDER BY issued_at DESC
    ''', (request.tenant_id,))
    
    rows = c.fetchall()
    conn.close()
    
    return jsonify({
        'invoices': [
            {
                'invoice_id': row[0],
                'amount_usd': row[1] / 100,
                'status': row[2],
                'issued_at': row[3],
                'due_date': row[4],
                'paid_at': row[5]
            } for row in rows
        ]
    })

@app.route('/api/v1/admin/tenants', methods=['GET'])
@require_admin
def list_all_tenants():
    """List all tenants (admin only)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT tenant_id, name, email, billing_tier, status, created_at
        FROM tenants
        ORDER BY created_at DESC
    ''')
    
    rows = c.fetchall()
    conn.close()
    
    return jsonify({
        'tenants': [
            {
                'tenant_id': row[0],
                'name': row[1],
                'email': row[2],
                'billing_tier': row[3],
                'status': row[4],
                'created_at': row[5]
            } for row in rows
        ]
    })

def create_tenant_namespace(tenant_id: str, name: str, billing_tier: str):
    """Create Kubernetes namespace for tenant"""
    try:
        template = '''
apiVersion: v1
kind: Namespace
metadata:
  name: tenant-{tenant_id}
  labels:
    tenant-id: "{tenant_id}"
    tenant-name: "{name}"
    billing-tier: "{billing_tier}"
'''
        config = template.format(tenant_id=tenant_id, name=name, billing_tier=billing_tier)
        
        result = subprocess.run(
            ['kubectl', 'apply', '-f', '-'],
            input=config.encode(),
            capture_output=True
        )
        
        if result.returncode != 0:
            logger.error(f"Failed to create namespace: {result.stderr.decode()}")
            raise Exception("Kubernetes namespace creation failed")
        
        logger.info(f"Created namespace for tenant {tenant_id}")
    except Exception as e:
        logger.error(f"Error creating tenant namespace: {e}")
        raise

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    init_db()
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=os.getenv('FLASK_ENV') == 'development'
    )
