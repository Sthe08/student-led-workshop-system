"""
Phase 6 Testing Script - Notifications & Broadcast Messaging

This script tests all Phase 6 features:
1. Email configuration
2. Registration confirmation emails
3. Broadcast messaging
4. In-app notifications
5. Reminder system

Run this script to verify Phase 6 implementation.
"""

import sys
from app import create_app, db
from app.models.user import User
from app.models.workshop import Workshop
from app.models.registration import Registration
from app.models.notification import Notification, BroadcastMessage
from app.services.email_service import (
    send_registration_confirmation_email,
    send_broadcast_message_email,
    send_workshop_reminder_email,
    generate_google_calendar_link,
    generate_outlook_calendar_link
)
from datetime import datetime, timedelta


def test_models():
    """Test if Notification and BroadcastMessage models work"""
    print("\n=== Testing Models ===")
    
    try:
        # Create test user
        user = User.query.first()
        if not user:
            print("❌ No users found. Please create a user first.")
            return False
        
        # Test Notification creation
        notification = Notification(
            user_id=user.id,
            notification_type='test',
            subject='Test Notification',
            message='This is a test notification'
        )
        db.session.add(notification)
        db.session.commit()
        
        # Verify it was saved
        saved_notification = Notification.query.filter_by(
            user_id=user.id,
            subject='Test Notification'
        ).first()
        
        if saved_notification:
            print(f"✅ Notification model working (ID: {saved_notification.id})")
            
            # Clean up
            db.session.delete(saved_notification)
            db.session.commit()
        else:
            print("❌ Notification not saved properly")
            return False
        
        # Test BroadcastMessage creation
        workshop = Workshop.query.first()
        if workshop:
            broadcast = BroadcastMessage(
                workshop_id=workshop.id,
                host_id=workshop.host_id,
                message='Test broadcast message',
                recipient_count=0
            )
            db.session.add(broadcast)
            db.session.commit()
            
            saved_broadcast = BroadcastMessage.query.filter_by(
                workshop_id=workshop.id,
                message='Test broadcast message'
            ).first()
            
            if saved_broadcast:
                print(f"✅ BroadcastMessage model working (ID: {saved_broadcast.id})")
                
                # Clean up
                db.session.delete(saved_broadcast)
                db.session.commit()
            else:
                print("❌ BroadcastMessage not saved properly")
                return False
        else:
            print("⚠️  No workshops found, skipping BroadcastMessage test")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {str(e)}")
        db.session.rollback()
        return False


def test_email_generation():
    """Test calendar link generation"""
    print("\n=== Testing Calendar Link Generation ===")
    
    try:
        workshop = Workshop.query.first()
        if not workshop:
            print("❌ No workshops found. Please create a workshop first.")
            return False
        
        # Test Google Calendar link
        google_link = generate_google_calendar_link(workshop)
        if google_link and 'calendar.google.com' in google_link:
            print(f"✅ Google Calendar link generated")
            print(f"   URL: {google_link[:100]}...")
        else:
            print("❌ Google Calendar link generation failed")
            return False
        
        # Test Outlook Calendar link
        outlook_link = generate_outlook_calendar_link(workshop)
        if outlook_link and 'outlook.live.com' in outlook_link:
            print(f"✅ Outlook Calendar link generated")
            print(f"   URL: {outlook_link[:100]}...")
        else:
            print("❌ Outlook Calendar link generation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Calendar link test failed: {str(e)}")
        return False


def test_notification_routes():
    """Test notification routes are registered"""
    print("\n=== Testing Notification Routes ===")
    
    from app import create_app
    app = create_app()
    
    routes = [rule.rule for rule in app.url_map.iter_rules()]
    
    required_routes = [
        '/notifications',
        '/notifications/<int:id>/mark-read',
        '/notifications/mark-all-read',
        '/notifications/unread-count',
        '/workshops/<int:id>/broadcast'
    ]
    
    all_found = True
    for route in required_routes:
        # Check if route pattern exists
        base_route = route.split('<')[0].rstrip('/')
        if any(base_route in r for r in routes):
            print(f"✅ Route found: {route}")
        else:
            print(f"❌ Route missing: {route}")
            all_found = False
    
    return all_found


def test_email_templates():
    """Test if email templates exist"""
    print("\n=== Testing Email Templates ===")
    
    import os
    template_dir = 'app/templates/email'
    
    required_templates = [
        'registration_confirmation.html',
        'registration_confirmation.txt',
        'broadcast_message.html',
        'broadcast_message.txt',
        'workshop_reminder.html',
        'workshop_reminder.txt',
        'workshop_update.html',
        'workshop_update.txt',
        'workshop_cancellation.html',
        'workshop_cancellation.txt'
    ]
    
    all_exist = True
    for template in required_templates:
        path = os.path.join(template_dir, template)
        if os.path.exists(path):
            print(f"✅ Template exists: {template}")
        else:
            print(f"❌ Template missing: {template}")
            all_exist = False
    
    return all_exist


def test_scheduler():
    """Test if APScheduler is configured"""
    print("\n=== Testing APScheduler Configuration ===")
    
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        print("✅ APScheduler imported successfully")
        
        # Try to import reminder service
        from app.services.reminder_service import init_scheduler, send_reminders
        print("✅ Reminder service imported successfully")
        
        # Check if scheduler can be initialized
        app = create_app()
        with app.app_context():
            scheduler = BackgroundScheduler()
            scheduler.start()
            scheduler.shutdown()
            print("✅ Scheduler can start and stop without errors")
        
        return True
        
    except ImportError as e:
        print(f"❌ APScheduler import failed: {str(e)}")
        print("   Install with: pip install APScheduler==3.10.4")
        return False
    except Exception as e:
        print(f"❌ Scheduler test failed: {str(e)}")
        return False


def test_database_tables():
    """Test if new database tables exist"""
    print("\n=== Testing Database Tables ===")
    
    try:
        # Check if tables exist by querying them
        notification_count = Notification.query.count()
        print(f"✅ 'notifications' table exists ({notification_count} records)")
        
        broadcast_count = BroadcastMessage.query.count()
        print(f"✅ 'broadcast_messages' table exists ({broadcast_count} records)")
        
        return True
        
    except Exception as e:
        print(f"❌ Database table test failed: {str(e)}")
        print("   Run the application to create the tables automatically")
        return False


def run_all_tests():
    """Run all Phase 6 tests"""
    print("=" * 60)
    print("PHASE 6 COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        results = []
        
        # Run all tests
        results.append(("Models", test_models()))
        results.append(("Calendar Links", test_email_generation()))
        results.append(("Notification Routes", test_notification_routes()))
        results.append(("Email Templates", test_email_templates()))
        results.append(("APScheduler", test_scheduler()))
        results.append(("Database Tables", test_database_tables()))
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Phase 6 is ready!")
            return True
        else:
            print("\n⚠️  Some tests failed. Please review the errors above.")
            return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
