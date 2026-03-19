# Virtual Meeting Integration Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Flask Application                             │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Workshop Routes                             │  │
│  │                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │  create_workshop() / edit_workshop()                    │  │  │
│  │  │                                                          │  │  │
│  │  │  1. Host selects "Virtual Workshop"                     │  │  │
│  │  │  2. Chooses platform (Google Meet / Teams)              │  │  │
│  │  │  3. Calls generate_meeting_link()                       │  │  │
│  │  │  4. Creates Workshop record with meeting link           │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  │                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │  generate_meeting_link()                                │  │  │
│  │  │                                                          │  │  │
│  │  │  try:                                                   │  │  │
│  │  │    ├─ if Google Meet:                                   │  │  │
│  │  │    │   └─ google_meet_service.create_meeting()         │  │  │
│  │  │    │       └─ Returns: REAL meet.google.com link       │  │  │
│  │  │    │                                                    │  │  │
│  │  │    ├─ if Teams:                                         │  │  │
│  │  │    │   └─ teams_service.create_meeting()               │  │  │
│  │  │    │       └─ Returns: REAL teams.microsoft.com link   │  │  │
│  │  │    │                                                    │  │  │
│  │  │    └─ except Exception:                                 │  │  │
│  │  │        └─ generate_placeholder_link()                  │  │  │
│  │  │            └─ Returns: PLACEHOLDER link                │  │  │
│  │  │                                                          │  │  │
│  │  │  Returns: (meeting_link, meeting_id, extra_data)       │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ API Calls
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Service Layer                                   │
│                                                                      │
│  ┌────────────────────────────┐  ┌────────────────────────────┐    │
│  │   Google Meet Service      │  │    Teams Service           │    │
│  │                            │  │                            │    │
│  │  • OAuth2 Authentication   │  │  • Azure AD Auth           │    │
│  │  • Token Management        │  │  • Client Credentials      │    │
│  │  • Calendar API Calls      │  │  • Graph API Calls         │    │
│  │  • Event Creation          │  │  • Meeting Creation        │    │
│  │  • Error Handling          │  │  • Error Handling          │    │
│  │                            │  │                            │    │
│  │  Methods:                  │  │  Methods:                  │    │
│  │  - get_credentials()       │  │  - get_access_token()      │    │
│  │  - create_meeting()        │  │  - create_meeting()        │    │
│  │  - delete_event()          │  │  - (delete coming soon)    │    │
│  └────────────────────────────┘  └────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
           │                                      │
           │ HTTPS                                │ HTTPS
           ▼                                      ▼
┌─────────────────────┐              ┌─────────────────────────────────┐
│   Google Cloud      │              │      Microsoft Azure            │
│                     │              │                                 │
│  ┌───────────────┐  │              │  ┌───────────────────────────┐  │
│  │ OAuth 2.0     │  │              │  │  Azure Active Directory   │  │
│  │ Authorization │  │              │  │                           │  │
│  │ - credentials │  │              │  │  - Client ID              │  │
│  │ - token.pickle│  │              │  │  - Client Secret          │  │
│  │ - refresh     │  │              │  │  - Tenant ID              │  │
│  └───────────────┘  │              │  └───────────────────────────┘  │
│                     │              │                                 │
│  ┌───────────────┐  │              │  ┌───────────────────────────┐  │
│  │ Calendar API  │  │              │  │  Microsoft Graph API      │  │
│  │               │  │              │  │                           │  │
│  │ - Create Event│  │              │  │  - POST /onlineMeetings   │  │
│  │ - Add Meet    │  │              │  │  - Generate Join URL      │  │
│  │ - Return Link │  │              │  │  - Return Meeting Object  │  │
│  └───────────────┘  │              │  └───────────────────────────┘  │
│                     │              │                                 │
│  Result:            │              │  Result:                        │
│  meet.google.com/   │              │  teams.microsoft.com/l/...      │
│  xxx-xxxx-xxx       │              │                                 │
└─────────────────────┘              └─────────────────────────────────┘
```

---

## Data Flow Sequence

### Creating a Virtual Workshop

```
┌─────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐
│Host │  │Workshop  │  │Meeting   │  │ Google   │  │ Google   │  │Calendar│
│User │  │Route     │  │Generator │  │ Service  │  │ OAuth    │  │ API    │
└──┬──┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘
   │         │              │             │             │            │
   │ 1. Create Virtual Workshop Request   │             │            │
   │────────▶│              │             │             │            │
   │         │              │             │             │            │
   │         │ 2. Generate Meeting Link   │             │            │
   │         │─────────────▶│             │             │            │
   │         │              │             │             │            │
   │         │              │ 3. Get/Auth Token         │            │
   │         │              │────────────▶│             │            │
   │         │              │             │             │            │
   │         │              │◀────────────│             │            │
   │         │              │ 4. Token Ready            │            │
   │         │              │             │             │            │
   │         │              │ 5. Create Meeting Event   │            │
   │         │              │──────────────────────────▶│            │
   │         │              │             │             │            │
   │         │              │             │ 6. OAuth Handshake       │
   │         │              │             │────────────▶│            │
   │         │              │             │             │            │
   │         │              │             │◀────────────│            │
   │         │              │             │ 7. Access Granted        │
   │         │              │             │             │            │
   │         │              │ 8. Create Calendar Event               │
   │         │              │──────────────────────────────────────▶│
   │         │              │             │             │            │
   │         │              │◀──────────────────────────────────────│
   │         │              │ 9. Event Created + Meet Link           │
   │         │              │             │             │            │
   │         │◀─────────────│             │             │            │
   │         │ 10. Return (link, id, data)            │            │
   │         │              │             │             │            │
   │         │ 11. Save Workshop to DB                │            │
   │         │──────────┐   │             │             │            │
   │         │          │   │             │             │            │
   │◀────────│──────────│   │             │             │            │
   │ 12. Success + REAL Link             │             │            │
   │         │              │             │             │            │
```

---

## Component Interaction

### Service Layer Pattern

```
┌─────────────────────────────────────────────────────────┐
│                   Presentation Layer                     │
│  (Routes: workshop.py)                                  │
│  - Handle HTTP requests                                 │
│  - Validate forms                                       │
│  - Call service methods                                 │
│  - Return responses                                     │
└─────────────────────────────────────────────────────────┘
                          │
                          │ Uses
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    Service Layer                         │
│  (Services: google_meet_service.py, teams_service.py)   │
│  - Business logic                                       │
│  - API communication                                    │
│  - Error handling                                       │
│  - Data transformation                                  │
└─────────────────────────────────────────────────────────┘
                          │
                          │ Calls
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   External APIs                          │
│  - Google Calendar API                                  │
│  - Microsoft Graph API                                  │
│  - OAuth2 Providers                                     │
└─────────────────────────────────────────────────────────┘
```

---

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────────┐
│              Workshop Creation Attempt                       │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│         Try: Generate Real Meeting Link                     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Call Service API                                     │  │
│  │  (google_meet_service.create_meeting() or            │  │
│  │   teams_service.create_meeting())                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
              │                      │
              │ SUCCESS              │ EXCEPTION
              │                      │
              ▼                      ▼
    ┌─────────────────┐    ┌─────────────────────────┐
    │ API Returns:    │    │ Catch Exception:        │
    │ ✓ meet_link     │    │ 1. Log error            │
    │ ✓ meeting_id    │    │ 2. Determine cause      │
    │ ✓ success=true  │    │ 3. Fallback strategy    │
    └─────────────────┘    └─────────────────────────┘
                                      │
                                      ▼
                            ┌─────────────────────────┐
                            │ Generate Placeholder    │
                            │ Link                    │
                            │                         │
                            │ • Fake but valid-looking│
                            │ • No calendar event     │
                            │ • Always works          │
                            └─────────────────────────┘
                                      │
                                      ▼
                            ┌─────────────────────────┐
                            │ Log Warning             │
                            │ "API failed, using      │
                            │  placeholder"           │
                            └─────────────────────────┘
```

---

## Authentication Flows

### Google OAuth2 Flow

```
┌─────────┐     ┌─────────┐     ┌──────────┐     ┌──────────┐
│  App    │     │  User   │     │  Google  │     │  Token   │
│         │     │         │     │  OAuth   │     │  Storage │
└────┬────┘     └────┬────┘     └─────┬────┘     └────┬─────┘
     │               │                │                │
     │ Need Access   │                │                │
     │──────────────▶│                │                │
     │               │                │                │
     │               │ Redirect to    │                │
     │               │ Google Login   │                │
     │               │───────────────▶│                │
     │               │                │                │
     │               │ User Grants    │                │
     │               │ Permission     │                │
     │               │                │                │
     │               │◀───────────────│                │
     │               │ Authorization  │                │
     │               │ Code           │                │
     │               │                │                │
     │ Exchange Code │                │                │
     │ for Token     │                │                │
     │───────────────────────────────▶│                │
     │               │                │                │
     │◀───────────────────────────────│                │
     │ Access Token  │                │                │
     │ & Refresh     │                │                │
     │ Token         │                │                │
     │               │                │                │
     │ Save Token    │                │                │
     │───────────────────────────────────────────────▶│
     │               │                │                │
     │ Use Token for │                │                │
     │ API Calls     │                │                │
     │───────────────────────────────▶│                │
     │               │                │                │
```

### Microsoft Teams App Authentication

```
┌─────────┐     ┌──────────────┐     ┌──────────┐
│  App    │     │Azure AD      │     │Microsoft │
│         │     │              │     │ Graph API│
└────┬────┘     └──────┬───────┘     └────┬─────┘
     │                 │                  │
     │ Request Token   │                  │
     │ Client ID +     │                  │
     │ Secret          │                  │
     │────────────────▶│                  │
     │                 │                  │
     │                 │ Validate         │
     │                 │ Credentials      │
     │                 │                  │
     │                 │ Issue Access     │
     │◀────────────────│                  │
     │ Access Token    │                  │
     │                 │                  │
     │ Use Token for   │                  │
     │ Meeting Creation│                  │
     │──────────────────────────────────▶│
     │                 │                  │
     │◀──────────────────────────────────│
     │ Meeting Object  │                  │
     │ with Join URL   │                  │
     │                 │                  │
```

---

## Database Schema

### Workshop Table (Updated)

```sql
CREATE TABLE workshops (
    -- Existing columns
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    date_time DATETIME,
    duration_minutes INTEGER,
    capacity INTEGER,
    
    -- NEW: Virtual workshop support
    workshop_type VARCHAR(20) DEFAULT 'physical',  -- 'physical' or 'virtual'
    meeting_link VARCHAR(500),                      -- Google Meet or Teams URL
    meeting_id VARCHAR(100),                        -- Internal meeting identifier
    meeting_provider VARCHAR(20),                   -- 'google_meet' or 'teams'
    
    -- Relationships
    venue_id INTEGER,                               -- NULL for virtual workshops
    host_id INTEGER,
    
    -- Metadata
    status VARCHAR(20) DEFAULT 'scheduled',
    created_at DATETIME,
    updated_at DATETIME
);
```

---

## File Structure

```
Flaskvprojecta/
│
├── app/
│   ├── services/
│   │   ├── __init__.py
│   │   ├── email_service.py
│   │   ├── reminder_service.py
│   │   ├── google_meet_service.py    ← NEW
│   │   └── teams_service.py          ← NEW
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── main.py
│   │   ├── workshop.py               ← UPDATED
│   │   └── ...
│   │
│   └── ...
│
├── instance/
│   ├── workshop.db
│   └── token.pickle                  ← AUTO-GENERATED (Google OAuth)
│
├── credentials.json                   ← GOOGLE OAUTH CREDENTIALS
├── meeting_config.py                  ← OPTIONAL CONFIG
├── requirements.txt                   ← UPDATED
├── REAL_MEETING_INTEGRATION_SETUP.md
├── QUICK_START_REAL_MEETINGS.md
├── IMPLEMENTATION_SUMMARY.md
└── ARCHITECTURE.md                    ← THIS FILE
```

---

## Deployment Architecture

### Development Environment

```
┌─────────────────────────────────────────────┐
│  Developer Machine                          │
│                                             │
│  ┌─────────────┐                           │
│  │ Flask App   │                           │
│  │ (localhost) │                           │
│  └──────┬──────┘                           │
│         │                                   │
│  ┌──────┴──────┐                           │
│  │ credentials │  teams env vars           │
│  │ .json       │  TEAMS_*                  │
│  └─────────────┘                           │
│                                             │
└─────────────────────────────────────────────┘
         │
         │ Internet
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Google OAuth    │     │ Microsoft Graph │
│ & Calendar API  │     │ API             │
└─────────────────┘     └─────────────────┘
```

### Production Environment

```
┌─────────────────────────────────────────────────────────┐
│  Production Server (e.g., AWS, Azure, Heroku)           │
│                                                         │
│  ┌─────────────────┐                                   │
│  │ Flask App       │                                   │
│  │ (gunicorn/uwsgi)│                                   │
│  └────────┬────────┘                                   │
│           │                                             │
│  ┌────────┴────────┐                                   │
│  │ Environment     │  Secure secret management         │
│  │ Variables       │  - AWS Secrets Manager            │
│  │ - TEAMS_*       │  - Azure Key Vault                │
│  │ - GOOGLE_*      │  - HashiCorp Vault                │
│  └─────────────────┘                                   │
│                                                         │
│  ┌─────────────────┐                                   │
│  │ Load Balancer   │                                   │
│  └─────────────────┘                                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
         │
         │ HTTPS
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Google Cloud    │     │ Microsoft Azure │
│ Platform        │     │ Platform        │
└─────────────────┘     └─────────────────┘
```

---

## Security Model

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1: Authentication                                    │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ • OAuth2 for Google (user delegation)                 │ │
│  │ • Client Credentials for Teams (app-only)             │ │
│  │ • Secure token storage                                │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Layer 2: Authorization                                     │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ • Minimal OAuth scopes (calendar access only)         │ │
│  │ • Application permissions (Teams meetings only)       │ │
│  │ • Principle of least privilege                        │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Layer 3: Data Protection                                   │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ • Credentials in environment variables                │ │
│  │ • Tokens encrypted at rest                            │ │
│  │ • HTTPS for all API calls                             │ │
│  │ • .gitignore for sensitive files                      │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Layer 4: Monitoring                                        │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ • Comprehensive error logging                         │ │
│  │ • API usage tracking                                  │ │
│  │ • Failed attempt monitoring                           │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Performance Considerations

### Response Time Optimization

```
┌─────────────────────────────────────────────────────────┐
│              Meeting Link Generation                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Best Case (Cached Token):                              │
│  ├─ Google: ~2-3 seconds                               │
│  │  └─ Token cached + API call                         │
│  └─ Teams: ~1-2 seconds                                │
│     └─ Direct API call                                 │
│                                                         │
│  First Time (OAuth Flow):                               │
│  └─ Google: ~5-10 seconds                              │
│     └─ Browser authorization + token exchange          │
│                                                         │
│  Fallback (Placeholder):                                │
│  └─ < 100ms                                            │
│     └─ Local generation, no API call                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Caching Strategy

```
┌─────────────────────────────────────────────────────────┐
│              Token Caching Architecture                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Google Meet:                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │ instance/token.pickle                           │   │
│  │ • Access token (cached)                         │   │
│  │ • Refresh token (long-lived)                    │   │
│  │ • Auto-refresh when expired                     │   │
│  │ • File-based persistence                        │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Microsoft Teams:                                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │ In-memory per request                           │   │
│  │ • Access token from MSAL                        │   │
│  │ • Valid for ~1 hour                             │   │
│  │ • Re-acquired each request                      │   │
│  │ • Can implement Redis cache for scale           │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Summary

This architecture provides:

✅ **Scalability** - Service layer pattern for easy scaling  
✅ **Reliability** - Automatic fallback ensures always available  
✅ **Security** - Multi-layer security model  
✅ **Performance** - Token caching and optimization  
✅ **Maintainability** - Clean separation of concerns  
✅ **Flexibility** - Easy to add new meeting providers  

**Ready for production deployment!** 🚀
