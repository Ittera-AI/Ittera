# Iterra Privacy & Security Whitepaper

## Executive Summary

Iterra is an AI Content Strategy Platform built with privacy-first principles. Unlike traditional SaaS platforms that store user data on centralized servers, Iterra leverages Google Drive for data storage, giving users full ownership and control over their content.

**Key Privacy Principles:**
- **Data Ownership**: Users own their data - we store it in their Google Drive
- **Minimal Data Collection**: We only store what's necessary for the service to function
- **Transparency**: Users can see exactly where their data is stored
- **Control**: Users can export, import, or delete their data at any time
- **Security**: Industry-standard encryption and security practices

---

## 1. Data Storage Architecture

### 1.1 Google Drive Integration (Privacy-First Design)

**Where Data Lives:**
```
User's Google Drive
├── Iterra/                          # Root folder created on connection
│   ├── scraped_posts.json          # Scraped social media data
│   ├── brand_analysis.json         # AI-generated brand analysis
│   ├── analytics_history.json      # Historical analytics
│   └── drafts/                     # Content drafts subfolder
│       ├── {draft-1}.json
│       ├── {draft-2}.json
│       └── ...
```

**Benefits of This Approach:**
- **User Ownership**: All content files are owned by the user in their Google Drive
- **No Vendor Lock-in**: Users can access their data directly in Drive without Iterra
- **Google's Security**: Inherits Google's security infrastructure
- **Automatic Backup**: Google Drive's backup and versioning applies
- **GDPR Compliance**: Data never leaves user's control

### 1.2 Iterra Database (Metadata Only)

**What We Store:**
- User account information (email, name, hashed password)
- Google Drive file IDs (to route requests)
- OAuth tokens (encrypted at rest)
- Storage preferences
- Content metadata (draft IDs, status, timestamps)

**What We DON'T Store:**
- Actual content drafts (stored in user's Drive)
- Scraped social media posts (stored in user's Drive)
- AI analysis results (stored in user's Drive)
- Raw analytics data (stored in user's Drive)

---

## 2. Security Measures

### 2.1 OAuth Token Encryption

**Problem**: OAuth tokens grant access to user's Google Drive. If compromised, attackers could access user data.

**Solution**: Fernet symmetric encryption using SHA-256 derived keys from application secret.

**Implementation**:
```python
# Tokens encrypted at rest
encrypted_token = encrypt_value(access_token)

# Tokens decrypted only when needed
decrypted_token = decrypt_value(encrypted_token)
```

**Key Derivation**:
```
SECRET_KEY (app secret)
    ↓ SHA-256
32-byte key
    ↓ base64.urlsafe_b64encode
Fernet-compatible key
```

### 2.2 Proactive Token Refresh

**Problem**: Access tokens expire, causing failures during operations.

**Solution**: Proactive refresh 5 minutes before expiry with exponential backoff retry.

**Flow**:
```
Before API Call:
  Check token expiry
    ↓
  If expires in < 5 minutes:
    Refresh using refresh_token
    ↓
  Execute API call
```

### 2.3 OAuth Scope Limitation

**Principle of Least Privilege**: We only request `drive.file` scope.

**What This Means**:
- Iterra can ONLY access files we created
- We cannot see user's other Drive files
- We cannot access user's Gmail, Calendar, etc.
- If user revokes access, we lose all access immediately

**Scope Details**:
```
https://www.googleapis.com/auth/drive.file
  ↳ Per-file access to files created by the app
  ↳ NOT full Drive access
```

### 2.4 Retry Logic with Exponential Backoff

**Purpose**: Handle transient failures without user intervention.

**Retry Conditions**:
- 5xx server errors
- Rate limiting (429)
- Connection timeouts
- SSL/network errors

**Backoff Strategy**:
```
Attempt 1: immediate
Attempt 2: wait 1 second
Attempt 3: wait 2 seconds
Attempt 4: wait 4 seconds
Max wait: 30 seconds
```

---

## 3. Privacy Controls

### 3.1 Granular Storage Preferences

**User Choice**: Users can choose storage location per content type.

**Options**:
- `google_drive`: Store in user's Google Drive (privacy-first)
- `local`: Download to local machine
- `ittera`: Store on Iterra servers (encrypted)

**Content Types**:
- Drafts
- Brand analysis
- Scraped posts
- Content calendar
- Reports
- Analytics

**Example Configuration**:
```json
{
  "default": "google_drive",
  "drafts": "google_drive",
  "analysis": "local",
  "scraped_posts": "google_drive"
}
```

### 3.2 Data Retention Policies

**User Control**: Define how long data is kept.

**Options**:
- `null`: Use system default (365 days)
- `0`: Never delete
- `7-3650`: Specific retention period

**Automatic Cleanup**:
- Runs weekly via Celery Beat
- Only deletes data older than retention period
- Never deletes from Google Drive (user's property)
- Only deletes Iterra-stored drafts without Drive file IDs

### 3.3 GDPR Compliance

**Article 15: Right of Access**
- Privacy dashboard shows all data locations
- `/api/v1/storage/privacy-dashboard` endpoint
- Transparent data inventory

**Article 17: Right to Erasure**
- `/api/v1/storage/data` DELETE endpoint
- Removes all files from user's Drive
- Clears file IDs from Iterra database
- Account remains (for re-connection)

**Article 20: Data Portability**
- `/api/v1/storage/export/download` endpoint
- Exports all data as structured JSON
- Includes metadata for re-import
- User can take data to another service

---

## 4. Audit & Transparency

### 4.1 Comprehensive Audit Logging

**What We Log**:
- Every Drive read operation
- Every Drive write operation
- Every Drive delete operation
- OAuth connections/disconnections
- Data exports (with file counts)
- Data imports
- Privacy setting changes

**What We DON'T Log**:
- Actual content (too large, user owns it)
- Encryption keys
- Passwords

**Log Format**:
```json
{
  "event_id": "uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "action": "storage:write",
  "user_id": "user-123",
  "resource_type": "drive_file",
  "resource_id": "file-456",
  "status": "success",
  "details": {
    "file_name": "brand_analysis.json",
    "operation": "create"
  }
}
```

### 4.2 Privacy Dashboard

**Purpose**: Show users exactly where their data lives.

**Features**:
- Data location inventory (Drive vs Iterra)
- Storage preferences display
- Connection status
- Pending operations count
- Retention policy info
- Data rights controls

---

## 5. Offline Operation Queue

### 5.1 Problem

Google Drive may be temporarily unavailable due to:
- Network issues
- Rate limiting
- Maintenance
- User revoked access

### 5.2 Solution

**Queue-Based Architecture**:
```
Drive Operation Fails
    ↓
Queue Operation in Redis
    ↓
Background Task Retries
    ↓
Success: Remove from Queue
Failure: Retry with Backoff
Max Retries: Move to Dead Letter
```

**Benefits**:
- User operations don't fail immediately
- Automatic recovery
- Transparent to user
- Durable (Redis-backed)

---

## 6. Security Best Practices

### 6.1 For Users

**Strong Recommendations**:
1. Use Google Drive for storage (privacy-first)
2. Enable 2FA on Google Account
3. Regularly review connected apps in Google Account
4. Export data periodically for backup

**Password Security**:
- Passwords hashed with bcrypt
- Salted per-user
- Work factor appropriate for 2024

### 6.2 For Developers

**Code Security**:
- No hardcoded secrets
- Environment variables for configuration
- `.env.example` committed, `.env` never committed
- Regular dependency updates

**API Security**:
- Rate limiting on all endpoints
- JWT authentication required
- Scope validation on OAuth tokens
- Input validation on all requests

---

## 7. Compliance Certifications

### 7.1 GDPR Compliance

| Article | Implementation |
|---------|---------------|
| 5 - Principles | Data minimization, accuracy, storage limitation |
| 15 - Access | Privacy dashboard, export functionality |
| 17 - Erasure | DELETE /storage/data endpoint |
| 20 - Portability | Export/download endpoint |
| 25 - Privacy by Design | Drive-first storage, granular preferences |
| 32 - Security | Encryption, token management, audit logs |

### 7.2 SOC 2 Type II (Planned)

**Controls Implemented**:
- Access controls (IAM)
- Change management (GitHub, PRs required)
- Data backup (Google Drive provides this)
- Incident response plan
- Audit logging

---

## 8. Incident Response

### 8.1 Data Breach Response

**If User's Drive Data is Exposed**:
1. We cannot access it (scope limitation)
2. User should revoke OAuth access
3. Notify Google if tokens compromised
4. User rotates Google password

**If Iterra Database is Breached**:
1. Tokens are encrypted - need SECRET_KEY to decrypt
2. File IDs are useless without Drive access
3. Passwords are hashed (bcrypt)
4. Force password reset for all users

### 8.2 Security Contact

For security issues:
- Email: security@iterra.ai
- GPG Key: Available on request
- Bug Bounty: Coming soon

---

## 9. Future Enhancements

### 9.1 Planned

- **End-to-End Encryption**: Encrypt content before sending to Drive
- **Multiple Storage Providers**: Dropbox, OneDrive support
- **Self-Hosted Option**: Run Iterra on your own infrastructure
- **Blockchain Anchoring**: Cryptographic proof of data existence

### 9.2 Under Consideration

- **Zero-Knowledge Architecture**: Iterra never sees unencrypted data
- **Federated Identity**: Login without Google
- **On-Premise AI**: Local LLM processing (privacy-maximal)

---

## 10. Summary

Iterra's privacy-first architecture ensures:

1. **You Own Your Data**: Stored in your Google Drive, not ours
2. **We Can't Access Other Files**: OAuth scope limitation
3. **Tokens Are Encrypted**: At rest with Fernet encryption
4. **Operations Are Logged**: For transparency and debugging
5. **You Control Retention**: Set your own data lifecycle
6. **You Can Export/Delete**: Full GDPR compliance
7. **Offline Resilience**: Queue-based retry system
8. **Minimal Data Collection**: Only metadata stored on Iterra

**Privacy is not a feature - it's the foundation.**

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Next Review**: Quarterly
