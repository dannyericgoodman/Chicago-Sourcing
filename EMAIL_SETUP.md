# Email Delivery Setup

Your daily founder report will be emailed to: **danny.eric.goodman@gmail.com**

## Quick Setup (5 minutes)

You need to add email credentials to GitHub Secrets so the workflow can send emails.

### Option 1: Gmail App Password (Recommended)

1. **Go to your Google Account**: https://myaccount.google.com/
2. **Enable 2-Step Verification** (if not already enabled):
   - Click "Security" → "2-Step Verification" → Follow setup
3. **Create App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select app: "Mail"
   - Select device: "Other (Custom name)" → Type: "GitHub Actions"
   - Click "Generate"
   - **Copy the 16-character password** (you'll need it in step 4)

4. **Add to GitHub Secrets**:
   - Go to: https://github.com/dannyericgoodman/Chicago-Sourcing/settings/secrets/actions
   - Click "New repository secret"
   - Add two secrets:

     **Secret 1:**
     - Name: `EMAIL_USERNAME`
     - Value: `danny.eric.goodman@gmail.com`

     **Secret 2:**
     - Name: `EMAIL_PASSWORD`
     - Value: (paste the 16-character app password from step 3)

5. **Done!** Run the workflow and you'll get the email.

### Option 2: Use a Different Email Service

If you don't want to use Gmail, you can use:
- **SendGrid** (free tier: 100 emails/day)
- **Mailgun** (free tier: 5000 emails/month)
- **AWS SES** (62,000 free emails/month)

Let me know if you want instructions for these.

## Testing

After adding the secrets:
1. Go to: https://github.com/dannyericgoodman/Chicago-Sourcing/actions
2. Click "Daily Sourcing Pipeline"
3. Click "Run workflow" → "Run workflow"
4. Wait 5 minutes
5. Check your email: danny.eric.goodman@gmail.com

## What You'll Receive

**Subject**: 🚀 Daily Founder Report - [Run Number]

**Email Content**:
- Beautiful HTML report (same as the artifact)
- Top 10 HIGH priority founders
- Top 10 MEDIUM priority founders
- Direct links to LinkedIn, Twitter, GitHub, Email
- AI reasoning for each match

**Frequency**: Every day at 6 AM CST (automatically)

## Troubleshooting

**Email not arriving?**
- Check spam/promotions folder
- Verify secrets are set correctly in GitHub
- Check workflow logs for errors

**Want to change email address?**
- Edit `.github/workflows/daily-sourcing.yml`
- Change line 81: `to: your-new-email@example.com`
- Commit and push

**Want to disable emails?**
- Comment out or remove the "Send Email Report" step in the workflow
- You'll still get the downloadable HTML report as an artifact
