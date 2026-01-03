#!/bin/bash
# Tenant Management Script for Zero-Day SaaS
# Usage: ./manage-tenant.sh create|delete|list|update <tenant-id> [options]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TENANT_TEMPLATE="${SCRIPT_DIR}/tenant-template.yaml"
REGISTRY_FILE="${SCRIPT_DIR}/.tenant-registry"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1" >&2
}

# Initialize registry
init_registry() {
    if [ ! -f "$REGISTRY_FILE" ]; then
        echo "TENANT_ID,TENANT_NAME,BILLING_TIER,NAMESPACE,CREATED_AT,STATUS" > "$REGISTRY_FILE"
    fi
}

# Create new tenant
create_tenant() {
    local tenant_id=$1
    local tenant_name=$2
    local billing_tier=${3:-basic}
    local storage_size=${4:-10Gi}
    
    if [ -z "$tenant_id" ] || [ -z "$tenant_name" ]; then
        log_error "Usage: create <tenant-id> <tenant-name> [billing-tier] [storage-size]"
        exit 1
    fi
    
    # Validate tenant ID (alphanumeric + hyphens only)
    if ! [[ "$tenant_id" =~ ^[a-z0-9-]+$ ]]; then
        log_error "Invalid tenant ID. Only lowercase alphanumeric and hyphens allowed."
        exit 1
    fi
    
    local namespace="tenant-${tenant_id}"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    log_info "Creating tenant: $tenant_id (name: $tenant_name, tier: $billing_tier)"
    
    # Process template
    local config=$(cat "$TENANT_TEMPLATE")
    config="${config//\{\{\ TENANT_ID\ \}\}/$tenant_id}"
    config="${config//\{\{\ TENANT_NAME\ \}\}/$tenant_name}"
    config="${config//\{\{\ BILLING_TIER\ \}}/\{\{\ BILLING_TIER\ \}\}/$billing_tier}"
    config="${config//\{\{\ TIMESTAMP\ \}\}/$timestamp}"
    config="${config//\{\{\ STORAGE_SIZE\ \}}/\{\{\ STORAGE_SIZE\ \}\}/$storage_size}"
    config="${config//\{\{\ TENANT_ADMIN_EMAIL\ \}}/admin@$tenant_id.local}"
    config="${config//\{\{\ RETENTION_DAYS\ \}}/30}"
    
    # Apply configuration
    echo "$config" | kubectl apply -f - 2>/dev/null || {
        log_error "Failed to create tenant namespace and resources"
        exit 1
    }
    
    # Add to registry
    echo "${tenant_id},${tenant_name},${billing_tier},${namespace},${timestamp},active" >> "$REGISTRY_FILE"
    
    log_success "Tenant created successfully"
    log_info "Namespace: $namespace"
    log_info "Billing Tier: $billing_tier"
    log_info "Storage: $storage_size"
    log_info ""
    log_info "Next steps:"
    log_info "1. Deploy graph-builder: kubectl apply -f graph-builder-tenant.yaml -n $namespace"
    log_info "2. Deploy inference: kubectl apply -f inference-tenant.yaml -n $namespace"
    log_info "3. Configure tenant with: kubectl set env deployment/graph-builder TENANT_ID=$tenant_id -n $namespace"
}

# List all tenants
list_tenants() {
    log_info "Registered Tenants:"
    if [ -f "$REGISTRY_FILE" ]; then
        column -t -s',' "$REGISTRY_FILE"
    else
        log_error "No tenants registered yet"
    fi
}

# Delete tenant
delete_tenant() {
    local tenant_id=$1
    
    if [ -z "$tenant_id" ]; then
        log_error "Usage: delete <tenant-id>"
        exit 1
    fi
    
    local namespace="tenant-${tenant_id}"
    
    log_info "Deleting tenant: $tenant_id"
    log_info "This will delete namespace: $namespace and all resources"
    read -p "Are you sure? (yes/no): " -r
    echo
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Cancelled"
        return
    fi
    
    kubectl delete namespace "$namespace" 2>/dev/null || {
        log_error "Failed to delete namespace: $namespace"
        exit 1
    }
    
    # Update registry
    if [ -f "$REGISTRY_FILE" ]; then
        sed -i.bak "/^${tenant_id},/s/active/deleted/" "$REGISTRY_FILE"
    fi
    
    log_success "Tenant deleted successfully"
}

# Get tenant status
get_tenant_status() {
    local tenant_id=$1
    
    if [ -z "$tenant_id" ]; then
        log_error "Usage: status <tenant-id>"
        exit 1
    fi
    
    local namespace="tenant-${tenant_id}"
    
    log_info "Tenant Status: $tenant_id"
    log_info ""
    log_info "Namespace Status:"
    kubectl get ns "$namespace" 2>/dev/null || {
        log_error "Namespace not found: $namespace"
        return
    }
    
    log_info ""
    log_info "Pods:"
    kubectl get pods -n "$namespace" 2>/dev/null || log_info "No pods found"
    
    log_info ""
    log_info "Resource Usage:"
    kubectl describe resourcequota -n "$namespace" 2>/dev/null || log_info "No quotas found"
    
    log_info ""
    log_info "Persistent Volumes:"
    kubectl get pvc -n "$namespace" 2>/dev/null || log_info "No PVCs found"
}

# Export tenant data (for backup)
export_tenant() {
    local tenant_id=$1
    local output_dir=${2:-.}
    
    if [ -z "$tenant_id" ]; then
        log_error "Usage: export <tenant-id> [output-dir]"
        exit 1
    fi
    
    local namespace="tenant-${tenant_id}"
    local export_file="${output_dir}/tenant-${tenant_id}-backup-$(date +%s).yaml"
    
    log_info "Exporting tenant data to: $export_file"
    kubectl get all -n "$namespace" -o yaml > "$export_file" 2>/dev/null || {
        log_error "Failed to export tenant"
        exit 1
    }
    
    log_success "Tenant exported successfully"
}

# Main
init_registry

case "${1:-help}" in
    create)
        create_tenant "$2" "$3" "$4" "$5"
        ;;
    list)
        list_tenants
        ;;
    delete)
        delete_tenant "$2"
        ;;
    status)
        get_tenant_status "$2"
        ;;
    export)
        export_tenant "$2" "$3"
        ;;
    help|*)
        echo "Zero-Day SaaS Tenant Management"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  create <tenant-id> <name> [tier] [size]  Create new tenant"
        echo "  list                                       List all tenants"
        echo "  delete <tenant-id>                         Delete tenant"
        echo "  status <tenant-id>                         Get tenant status"
        echo "  export <tenant-id> [dir]                   Export tenant backup"
        echo ""
        echo "Examples:"
        echo "  $0 create acme-corp 'ACME Corp' enterprise 50Gi"
        echo "  $0 status acme-corp"
        echo "  $0 list"
        ;;
esac
