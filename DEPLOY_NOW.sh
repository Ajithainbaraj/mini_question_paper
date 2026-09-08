#!/bin/bash
# Quick Deployment Script for EduAI with Question Variations Feature

echo "🚀 EduAI Deployment Script"
echo "=========================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check git status
echo "📋 Step 1: Checking git status..."
git status

echo ""
echo -e "${YELLOW}Files ready to commit?${NC}"
read -p "Continue? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo -e "${RED}Deployment cancelled.${NC}"
    exit 1
fi

# Step 2: Add all files
echo ""
echo "📦 Step 2: Adding files to git..."
git add .

# Step 3: Commit changes
echo ""
echo "💾 Step 3: Committing changes..."
echo "Enter commit message (or press Enter for default):"
read -r commit_message

if [ -z "$commit_message" ]
then
    commit_message="Add Question Variations feature and update LLM model to openai/gpt-oss-120b"
fi

git commit -m "$commit_message"

# Step 4: Show remote
echo ""
echo "📡 Step 4: Git remotes:"
git remote -v

echo ""
echo -e "${YELLOW}Which remote do you want to push to?${NC}"
echo "1) origin (GitHub/GitLab/etc - for Render auto-deploy)"
echo "2) heroku (Heroku deployment)"
echo "3) both"
read -p "Select (1/2/3): " -n 1 -r remote_choice
echo

# Step 5: Push
echo ""
echo "🚀 Step 5: Pushing to remote..."

case $remote_choice in
    1)
        echo "Pushing to origin..."
        git push origin main
        ;;
    2)
        echo "Pushing to heroku..."
        git push heroku main
        ;;
    3)
        echo "Pushing to origin..."
        git push origin main
        echo "Pushing to heroku..."
        git push heroku main
        ;;
    *)
        echo -e "${RED}Invalid choice. Exiting.${NC}"
        exit 1
        ;;
esac

# Step 6: Success message
echo ""
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo ""
echo "📝 Next Steps:"
echo "1. Monitor deployment logs on your platform"
echo "2. Wait for deployment to complete (5-15 minutes)"
echo "3. Test your application"
echo "4. Verify Question Variations feature works"
echo ""
echo "🔗 Common URLs:"
echo "  Render Dashboard: https://dashboard.render.com"
echo "  Heroku Dashboard: https://dashboard.heroku.com"
echo ""
echo "📖 See DEPLOYMENT_GUIDE.md for troubleshooting"
echo ""
