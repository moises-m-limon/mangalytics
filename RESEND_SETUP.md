# resend email setup

guide for configuring resend to send emails from your own domain.

## current limitation

with the default `onboarding@resend.dev` email address:
- ✅ you can send to **moises.m.limon@gmail.com** (your verified email)
- ❌ you **cannot** send to other email addresses

## testing with default setup

for testing, update your subscription to use your own email:

```json
{
  "email": "moises.m.limon@gmail.com",
  "topic": "LLMs"
}
```

this will work immediately without any domain verification.

## production setup: verify a custom domain

to send emails to any recipient, you need to verify a domain.

### step 1: choose a domain

you need access to a domain's DNS settings. options:
- **existing domain**: use a domain you already own (e.g., example.com)
- **subdomain**: create a subdomain (e.g., mail.example.com)
- **new domain**: purchase a cheap domain ($10-15/year)

recommended registrars:
- namecheap
- google domains
- cloudflare

### step 2: verify domain in resend

1. go to https://resend.com/domains
2. click "add domain"
3. enter your domain (e.g., mangalytics.com or mail.yourdomain.com)
4. resend will provide dns records to add

### step 3: add dns records

resend will give you dns records like:

**spf record (txt):**
```
Name: @
Type: TXT
Value: v=spf1 include:resend.com ~all
```

**dkim records (cname):**
```
Name: resend._domainkey
Type: CNAME
Value: resend1.resend.com

Name: resend2._domainkey
Type: CNAME
Value: resend2.resend.com
```

**dmarc record (txt):**
```
Name: _dmarc
Type: TXT
Value: v=DMARC1; p=none;
```

add these records in your domain registrar's dns settings.

### step 4: wait for verification

- dns propagation takes 5-60 minutes
- resend will automatically verify once dns is updated
- you'll get an email when verification is complete

### step 5: update environment variable

once verified, update your `.env` file:

```bash
# replace onboarding@resend.dev with your verified domain
RESEND_FROM_EMAIL=mangalytics <noreply@yourdomain.com>
```

or use any email from your verified domain:
```bash
RESEND_FROM_EMAIL=mangalytics <hello@yourdomain.com>
RESEND_FROM_EMAIL=research digest <digest@yourdomain.com>
RESEND_FROM_EMAIL=no-reply@yourdomain.com
```

### step 6: restart backend

```bash
# restart the backend to load new env variable
python -m app.main
```

now you can send to any email address!

## example domain setups

### option 1: subdomain (recommended)

if you own `example.com`, create `mail.example.com`:

1. verify `mail.example.com` in resend
2. add dns records for `mail.example.com`
3. set `RESEND_FROM_EMAIL=mangalytics <noreply@mail.example.com>`

**pros:**
- doesn't affect main domain
- can use different email service for main domain
- easy to manage

### option 2: full domain

verify `example.com`:

1. verify `example.com` in resend
2. add dns records for `example.com`
3. set `RESEND_FROM_EMAIL=mangalytics <noreply@example.com>`

**pros:**
- cleaner email addresses
- professional appearance

**cons:**
- affects main domain's email setup

### option 3: new domain

purchase `mangalytics.com`:

1. buy domain at namecheap ($10-15)
2. verify `mangalytics.com` in resend
3. add dns records
4. set `RESEND_FROM_EMAIL=mangalytics <digest@mangalytics.com>`

**pros:**
- dedicated domain for the service
- no conflicts with existing email
- branded email addresses

## dns configuration examples

### namecheap

1. go to namecheap dashboard
2. click "manage" next to your domain
3. go to "advanced dns" tab
4. click "add new record"
5. add the txt and cname records from resend

### cloudflare

1. go to cloudflare dashboard
2. select your domain
3. go to "dns" section
4. click "add record"
5. add the txt and cname records from resend

### google domains

1. go to google domains
2. select your domain
3. click "dns" in the sidebar
4. scroll to "custom resource records"
5. add the txt and cname records from resend

## troubleshooting

### dns not propagating

**wait longer:**
- dns can take up to 48 hours (usually 5-60 minutes)
- check status: https://dnschecker.org

**verify records:**
```bash
# check spf
dig yourdomain.com TXT

# check dkim
dig resend._domainkey.yourdomain.com CNAME

# check dmarc
dig _dmarc.yourdomain.com TXT
```

### verification failed

**common issues:**
- typo in dns records
- @ symbol not supported (use blank or domain name)
- trailing dots in cname values (remove them)
- caching issues (clear dns cache)

**fix:**
1. double-check all dns records match resend exactly
2. remove any trailing periods
3. wait 30 minutes and try again

### emails going to spam

**improve deliverability:**
1. verify spf, dkim, and dmarc are all set up
2. set dmarc policy to `p=quarantine` or `p=reject`
3. add domain to resend's "domain reputation"
4. warm up domain by sending to engaged recipients first
5. ask recipients to whitelist your email

### still using onboarding@resend.dev

**error message:**
```
You can only send testing emails to your own email address (moises.m.limon@gmail.com)
```

**solution:**
- verify you updated `.env` file
- restart backend after changing `.env`
- check resend dashboard shows domain as "verified"

## cost

resend pricing:
- **free tier**: 3,000 emails/month
- **pro tier**: $20/month for 50,000 emails/month

domain cost:
- **purchase**: $10-15/year
- **dns hosting**: free with most registrars

## alternative: free testing

if you don't want to verify a domain yet:

**option 1:** always test with your own email
```bash
# frontend form
email: moises.m.limon@gmail.com
topic: LLMs
```

**option 2:** use email testing service
- mailtrap.io (development email testing)
- mailhog (local email testing)
- papercut (local smtp server)

**option 3:** mock email service for development
```python
# in app/services/resend_email.py for testing
if os.getenv("ENV") == "development":
    print(f"[MOCK] Would send email to {to_email}")
    return {"success": True, "email_id": "mock-123"}
```

## production checklist

- [ ] purchase or select domain
- [ ] verify domain in resend dashboard
- [ ] add spf txt record
- [ ] add dkim cname records (2 records)
- [ ] add dmarc txt record
- [ ] wait for dns propagation
- [ ] confirm verification in resend dashboard
- [ ] update `RESEND_FROM_EMAIL` in `.env`
- [ ] restart backend service
- [ ] test sending to different email address
- [ ] check spam folder if not received
- [ ] ask recipient to whitelist domain

## support

- resend docs: https://resend.com/docs
- resend domains: https://resend.com/domains
- resend support: support@resend.com
- dns checker: https://dnschecker.org
