"""
Microsoft Teams Service
Integrates with Microsoft Graph API to create real Teams meeting links
"""
import requests
from datetime import datetime, timedelta
from flask import current_app
import msal


class TeamsMeetingService:
    """Service for creating Microsoft Teams meeting links via Microsoft Graph API"""
    
    def __init__(self):
        self.client_id = None
        self.client_secret = None
        self.tenant_id = None
        self.scope = 'https://graph.microsoft.com/.default'
        
    def configure(self, client_id, client_secret, tenant_id):
        """Configure the service with Azure AD credentials"""
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
    
    def get_access_token(self):
        """Get Microsoft Graph API access token using client credentials"""
        if not all([self.client_id, self.client_secret, self.tenant_id]):
            raise Exception("Teams service not configured. Set TEAMS_CLIENT_ID, TEAMS_CLIENT_SECRET, TEAMS_TENANT_ID environment variables.")
        
        authority = f'https://login.microsoftonline.com/{self.tenant_id}'
        
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=authority,
            client_credential=self.client_secret
        )
        
        result = app.acquire_token_for_client(scopes=[self.scope])
        
        if 'access_token' in result:
            return result['access_token']
        else:
            error_msg = result.get('error_description', 'Unknown error acquiring token')
            current_app.logger.error(f'Token acquisition error: {error_msg}')
            raise Exception(f"Error acquiring token: {error_msg}")
    
    def create_meeting(self, title, start_time, duration_minutes, description='', organizer_email=None):
        """
        Create a Teams meeting via Microsoft Graph API
        
        Args:
            title: Meeting subject
            start_time: datetime object
            duration_minutes: int
            description: Meeting description
            organizer_email: Email of the organizer (not used with app-only auth)
            
        Returns:
            dict with join_url, meeting_id, success
        """
        try:
            access_token = self.get_access_token()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            # Use application permissions (no user context needed)
            endpoint = 'https://graph.microsoft.com/v1.0/communications/onlineMeetings'
            
            data = {
                'subject': title,
                'startDateTime': start_time.isoformat(),
                'endDateTime': end_time.isoformat(),
                'externalId': f'workshop-{start_time.timestamp()}'
            }
            
            response = requests.post(endpoint, json=data, headers=headers)
            response.raise_for_status()
            
            meeting = response.json()
            
            current_app.logger.info(f'Teams meeting created: {meeting.get("joinUrl")}')
            
            return {
                'join_url': meeting.get('joinUrl'),
                'meeting_id': meeting.get('id'),
                'audio_conference_id': meeting.get('audioConferencing', {}).get('conferenceId'),
                'success': True
            }
            
        except requests.exceptions.HTTPError as error:
            error_text = error.response.text if hasattr(error.response, 'text') else str(error)
            current_app.logger.error(f'Teams API HTTP error: {error_text}')
            return {
                'success': False,
                'error': f'HTTP Error: {error_text}'
            }
        except Exception as e:
            current_app.logger.error(f'Unexpected error in Teams service: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }


# Singleton instance
teams_service = TeamsMeetingService()
