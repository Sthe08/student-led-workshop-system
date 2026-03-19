"""
Google Meet Service
Integrates with Google Calendar API to create real Google Meet links
"""
import os
import pickle
from datetime import datetime, timedelta
from flask import current_app
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleMeetService:
    """Service for creating Google Meet links via Google Calendar API"""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self):
        self.creds = None
        self.token_path = 'instance/token.pickle'
        self.credentials_path = 'credentials.json'
        
    def get_credentials(self):
        """Get valid user credentials from storage or flow"""
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                self.creds = pickle.load(token)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if os.path.exists(self.credentials_path):
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES)
                    self.creds = flow.run_local_server(port=0, open_browser=True)
                else:
                    raise Exception("credentials.json not found. Please set up Google Calendar API.")
            
            with open(self.token_path, 'wb') as token:
                pickle.dump(self.creds, token)
        
        return self.creds
    
    def create_meeting(self, title, start_time, duration_minutes, description='', attendees=None):
        """
        Create a Google Calendar event with Meet link
        
        Args:
            title: Event title
            start_time: datetime object
            duration_minutes: int
            description: Event description
            attendees: List of email addresses
            
        Returns:
            dict with meet_link, meeting_id, hangout_link
        """
        try:
            creds = self.get_credentials()
            service = build('calendar', 'v3', credentials=creds)
            
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'conferenceData': {
                    'createRequest': {
                        'requestId': f'meeting-{start_time.timestamp()}',
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                        'status': {'statusCode': 'success'}
                    }
                },
            }
            
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            event = service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1
            ).execute()
            
            current_app.logger.info(f'Google Meet created: {event.get("hangoutLink")}')
            
            return {
                'meet_link': event.get('hangoutLink'),
                'meeting_id': event.get('conferenceData', {}).get('conferenceId', ''),
                'event_id': event['id'],
                'success': True
            }
            
        except HttpError as error:
            current_app.logger.error(f'Google Meet API error: {error}')
            return {
                'success': False,
                'error': str(error)
            }
        except Exception as e:
            current_app.logger.error(f'Unexpected error in Google Meet service: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_event(self, event_id):
        """Delete a calendar event"""
        try:
            creds = self.get_credentials()
            service = build('calendar', 'v3', credentials=creds)
            
            service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            current_app.logger.info(f'Google Calendar event deleted: {event_id}')
            return {'success': True}
            
        except Exception as e:
            current_app.logger.error(f'Error deleting Google Calendar event: {str(e)}')
            return {'success': False, 'error': str(e)}


# Singleton instance
google_meet_service = GoogleMeetService()
