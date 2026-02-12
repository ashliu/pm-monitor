#!/bin/bash
# Gitea CLI Helper
# Usage: ./gitea.sh [list-repos|list-issues|create-issue|...]

# Load config
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/.gitea_env" ]; then
    source "$SCRIPT_DIR/.gitea_env"
else
    echo "Error: .gitea_env not found"
    exit 1
fi

# Check required vars
if [ -z "$GITEA_API_TOKEN" ] || [ -z "$GITEA_URL" ]; then
    echo "Error: GITEA_API_TOKEN or GITEA_URL not set"
    exit 1
fi

# API base
API_BASE="$GITEA_URL/api/v1"
AUTH_HEADER="Authorization: token $GITEA_API_TOKEN"

# Functions
cmd_list_repos() {
    echo "Listing your repositories..."
    curl -s -H "$AUTH_HEADER" "$API_BASE/user/repos" | python3 -m json.tool 2>/dev/null || curl -s -H "$AUTH_HEADER" "$API_BASE/user/repos"
}

cmd_list_issues() {
    local owner="${1:-}"
    local repo="${2:-}"
    
    if [ -z "$owner" ] || [ -z "$repo" ]; then
        echo "Usage: $0 list-issues <owner> <repo>"
        echo "Example: $0 list-issues ashliu myproject"
        exit 1
    fi
    
    echo "Listing issues for $owner/$repo..."
    curl -s -H "$AUTH_HEADER" "$API_BASE/repos/$owner/$repo/issues" | python3 -m json.tool 2>/dev/null || curl -s -H "$AUTH_HEADER" "$API_BASE/repos/$owner/$repo/issues"
}

cmd_create_issue() {
    local owner="${1:-}"
    local repo="${2:-}"
    local title="${3:-}"
    local body="${4:-}"
    
    if [ -z "$owner" ] || [ -z "$repo" ] || [ -z "$title" ]; then
        echo "Usage: $0 create-issue <owner> <repo> <title> [body]"
        echo "Example: $0 create-issue ashliu myproject 'Bug report' 'Something is broken'"
        exit 1
    fi
    
    local json_body="{\"title\": \"$title\", \"body\": \"${body:-}\"}"
    
    echo "Creating issue in $owner/$repo..."
    curl -s -X POST -H "$AUTH_HEADER" -H "Content-Type: application/json" -d "$json_body" "$API_BASE/repos/$owner/$repo/issues" | python3 -m json.tool 2>/dev/null || curl -s -X POST -H "$AUTH_HEADER" -H "Content-Type: application/json" -d "$json_body" "$API_BASE/repos/$owner/$repo/issues"
}

cmd_close_issue() {
    local owner="${1:-}"
    local repo="${2:-}"
    local issue_num="${3:-}"
    
    if [ -z "$owner" ] || [ -z "$repo" ] || [ -z "$issue_num" ]; then
        echo "Usage: $0 close-issue <owner> <repo> <issue_number>"
        exit 1
    fi
    
    echo "Closing issue #$issue_num in $owner/$repo..."
    curl -s -X PATCH -H "$AUTH_HEADER" -H "Content-Type: application/json" -d '{"state": "closed"}' "$API_BASE/repos/$owner/$repo/issues/$issue_num" | python3 -m json.tool 2>/dev/null || curl -s -X PATCH -H "$AUTH_HEADER" -H "Content-Type: application/json" -d '{"state": "closed"}' "$API_BASE/repos/$owner/$repo/issues/$issue_num"
}

cmd_user_info() {
    echo "Getting user info..."
    curl -s -H "$AUTH_HEADER" "$API_BASE/user" | python3 -m json.tool 2>/dev/null || curl -s -H "$AUTH_HEADER" "$API_BASE/user"
}

# Main
case "${1:-}" in
    list-repos)
        cmd_list_repos
        ;;
    list-issues)
        cmd_list_issues "$2" "$3"
        ;;
    create-issue)
        cmd_create_issue "$2" "$3" "$4" "$5"
        ;;
    close-issue)
        cmd_close_issue "$2" "$3" "$4"
        ;;
    user-info)
        cmd_user_info
        ;;
    *)
        echo "Gitea CLI Helper"
        echo ""
        echo "Usage: $0 <command> [args...]"
        echo ""
        echo "Commands:"
        echo "  user-info                Show current user info"
        echo "  list-repos               List your repositories"
        echo "  list-issues <owner> <repo>  List issues in a repository"
        echo "  create-issue <owner> <repo> <title> [body]  Create a new issue"
        echo "  close-issue <owner> <repo> <issue_num>  Close an issue"
        echo ""
        echo "Examples:"
        echo "  $0 user-info"
        echo "  $0 list-repos"
        echo "  $0 list-issues ashliu myproject"
        echo "  $0 create-issue ashliu myproject 'Bug: something broken' 'Description here'"
        exit 1
        ;;
esac
