"""
Locust-based load generator for Elgg Web 2.0 Benchmark
Replaces the Faban-based Web20Driver.java

This generator simulates realistic user behavior on an Elgg social network,
including login, profile management, messaging, blogging, and activity feeds.

Author: Converted from Web20Driver.java (Tapti Palit, Ali Ansari)
"""

import json
import logging
import random
import re
import string
from typing import Dict, List, Optional

from locust import HttpUser, between, task, TaskSet, events
from locust.contrib.fasthttp import FastHttpUser


logger = logging.getLogger(__name__)


class ElggUser:
    """Represents an Elgg user with state management"""
    
    def __init__(self, username: str, password: str, guid: Optional[str] = None):
        self.username = username
        self.password = password
        self.guid = guid
        self.email = ""
        self.elgg_token = ""
        self.elgg_ts = ""
        self.logged_in = False
        
        # User-generated content tracking
        self.friends_list: List[str] = []
        self.messages_guids: List[str] = []
        self.blogs_guids: List[str] = []
        self.wires_guids: List[str] = []
        self.num_activities = 0


class RandomStringGenerator:
    """Generate random strings for user-generated content"""
    
    @staticmethod
    def generate_random_string(length: int = 15, mode: str = "alpha") -> str:
        """
        Generate random string
        
        Args:
            length: Length of the string
            mode: "alpha" for letters only, "alphanumeric" for letters+digits
        """
        if mode == "alpha":
            chars = string.ascii_letters
        else:
            chars = string.ascii_letters + string.digits
        
        return ''.join(random.choice(chars) for _ in range(length))


class ElggBehavior(TaskSet):
    """Defines all Elgg benchmark operations as tasks"""
    
    def on_start(self):
        """Called when a simulated user starts"""
        self.elgg_user = ElggUser("", "")
        self.setup_user()
        self.browse_to_elgg()
    
    def setup_user(self):
        """Load a user from the users list"""
        try:
            with open("/app/users.list", "r") as f:
                users = f.readlines()
                if users:
                    user_line = random.choice(users).strip()
                    parts = user_line.split(":")
                    if len(parts) >= 2:
                        self.elgg_user.username = parts[0]
                        self.elgg_user.password = parts[1]
                        if len(parts) >= 3:
                            self.elgg_user.guid = parts[2]
        except FileNotFoundError:
            logger.warning("users.list not found, using default users")
            self.elgg_user.username = f"user{random.randint(1, 1000)}"
            self.elgg_user.password = "password"
    
    def extract_elgg_token_and_ts(self, response_text: str) -> tuple:
        """Extract __elgg_token and __elgg_ts from response"""
        try:
            # Try JSON parsing first
            token_match = re.search(r'"__elgg_token":"([^"]+)"', response_text)
            ts_match = re.search(r'"__elgg_ts":(\d+)', response_text)
            
            if token_match and ts_match:
                token = token_match.group(1)
                ts = ts_match.group(1)
                return token, ts
        except Exception as e:
            logger.debug(f"Error extracting token: {e}")
        
        return "", ""
    
    @task(100)
    def browse_to_elgg(self):
        """Browse to Elgg home page"""
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.extract_elgg_token_and_ts(response.text)
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(100)
    def do_login(self):
        """Login with user credentials"""
        if self.elgg_user.logged_in:
            return
        
        # Get login page first to extract token
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                self.elgg_user.elgg_token, self.elgg_user.elgg_ts = self.extract_elgg_token_and_ts(response.text)
        
        # Perform login
        login_data = {
            "username": self.elgg_user.username,
            "password": self.elgg_user.password,
            "__elgg_token": self.elgg_user.elgg_token,
            "__elgg_ts": self.elgg_user.elgg_ts,
        }
        
        with self.client.post("/action/login", data=login_data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.elgg_user.logged_in = True
                self.extract_elgg_token_and_ts(response.text)
            else:
                response.failure(f"Login failed with status {response.status_code}")
    
    @task(5)
    def register(self):
        """Register a new user"""
        # Get registration page
        with self.client.get("/register", catch_response=True) as response:
            if response.status_code == 200:
                token, ts = self.extract_elgg_token_and_ts(response.text)
            else:
                response.failure(f"Failed to get registration page: {response.status_code}")
                return
        
        # Register new user
        new_username = f"newuser_{random.randint(10000, 99999)}"
        new_password = RandomStringGenerator.generate_random_string(12)
        new_email = f"{new_username}@example.com"
        
        register_data = {
            "username": new_username,
            "password": new_password,
            "password2": new_password,
            "email": new_email,
            "name": new_username,
            "__elgg_token": token,
            "__elgg_ts": ts,
        }
        
        with self.client.post("/action/register", data=register_data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Registration failed with status {response.status_code}")
    
    @task(5)
    def logout(self):
        """Logout the current user"""
        if not self.elgg_user.logged_in:
            return
        
        with self.client.get("/action/logout", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.elgg_user.logged_in = False
            else:
                response.failure(f"Logout failed with status {response.status_code}")
    
    @task(5)
    def add_friend(self):
        """Send a friend request"""
        if not self.elgg_user.logged_in or len(self.elgg_user.friends_list) >= 50:
            return
        
        random_user_guid = self._get_random_user_guid()
        if not random_user_guid:
            return
        
        friend_data = {
            "__elgg_token": self.elgg_user.elgg_token,
            "__elgg_ts": self.elgg_user.elgg_ts,
            "friend": random_user_guid,
        }
        
        with self.client.post("/action/friends/add", data=friend_data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                if random_user_guid not in self.elgg_user.friends_list:
                    self.elgg_user.friends_list.append(random_user_guid)
            else:
                response.failure(f"Add friend failed with status {response.status_code}")
    
    @task(5)
    def remove_friend(self):
        """Remove a friend"""
        if not self.elgg_user.logged_in or not self.elgg_user.friends_list:
            return
        
        friend_guid = random.choice(self.elgg_user.friends_list)
        
        remove_data = {
            "__elgg_token": self.elgg_user.elgg_token,
            "__elgg_ts": self.elgg_user.elgg_ts,
            "friend": friend_guid,
        }
        
        with self.client.post("/action/friends/remove", data=remove_data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.elgg_user.friends_list.remove(friend_guid)
            else:
                response.failure(f"Remove friend failed with status {response.status_code}")
    
    @task(5)
    def check_activity(self):
        """Check recent activities"""
        if not self.elgg_user.logged_in:
            return
        
        activity_url = random.choice(["/activity", "/activity/owner/", "/activity/friends/"])
        
        with self.client.get(activity_url, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.extract_elgg_token_and_ts(response.text)
            else:
                response.failure(f"Check activity failed with status {response.status_code}")
    
    @task(5)
    def dashboard(self):
        """Access user dashboard"""
        if not self.elgg_user.logged_in:
            return
        
        with self.client.get("/dashboard", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.extract_elgg_token_and_ts(response.text)
            else:
                response.failure(f"Dashboard access failed with status {response.status_code}")
    
    @task(5)
    def access_home_page(self):
        """Access home page"""
        if not self.elgg_user.logged_in:
            return
        
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.extract_elgg_token_and_ts(response.text)
            else:
                response.failure(f"Home page access failed with status {response.status_code}")
    
    @task(5)
    def get_notifications(self):
        """Get user notifications"""
        if not self.elgg_user.logged_in:
            return
        
        with self.client.get(f"/site_notifications/owner/{self.elgg_user.username}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.extract_elgg_token_and_ts(response.text)
            else:
                response.failure(f"Get notifications failed with status {response.status_code}")
    
    @task(5)
    def inbox(self):
        """Access user inbox"""
        if not self.elgg_user.logged_in:
            return
        
        with self.client.get(f"/messages/inbox/{self.elgg_user.username}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.extract_elgg_token_and_ts(response.text)
            else:
                response.failure(f"Inbox access failed with status {response.status_code}")
    
    @task(5)
    def check_profile(self):
        """Check a user's profile"""
        if not self.elgg_user.logged_in:
            return
        
        random_user_name = self._get_random_user_name()
        if not random_user_name:
            return
        
        with self.client.get(f"/profile/{random_user_name}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.extract_elgg_token_and_ts(response.text)
            else:
                response.failure(f"Profile check failed with status {response.status_code}")
    
    @task(5)
    def check_friends(self):
        """Check friends list"""
        if not self.elgg_user.logged_in:
            return
        
        random_user_name = self._get_random_user_name()
        if not random_user_name:
            return
        
        with self.client.get(f"/friends/{random_user_name}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.extract_elgg_token_and_ts(response.text)
            else:
                response.failure(f"Check friends failed with status {response.status_code}")
    
    @task(5)
    def check_wire(self):
        """Check wire posts"""
        if not self.elgg_user.logged_in:
            return
        
        wire_url = random.choice(["/thewire", "/thewire/owner/", "/thewire/friends/"])
        
        with self.client.get(wire_url, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.extract_elgg_token_and_ts(response.text)
            else:
                response.failure(f"Check wire failed with status {response.status_code}")
    
    @task(5)
    def post_wire(self):
        """Post a wire message"""
        if not self.elgg_user.logged_in:
            return
        
        wire_content = RandomStringGenerator.generate_random_string(15, "alpha")
        
        wire_data = {
            "__elgg_token": self.elgg_user.elgg_token,
            "__elgg_ts": self.elgg_user.elgg_ts,
            "body": wire_content,
        }
        
        with self.client.post("/action/thewire/add", data=wire_data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.extract_elgg_token_and_ts(response.text)
            else:
                response.failure(f"Post wire failed with status {response.status_code}")
    
    @task(5)
    def reply_wire(self):
        """Reply to a wire"""
        if not self.elgg_user.logged_in or not self.elgg_user.wires_guids:
            return
        
        wire_guid = random.choice(self.elgg_user.wires_guids)
        reply_content = RandomStringGenerator.generate_random_string(15, "alpha")
        
        reply_data = {
            "__elgg_token": self.elgg_user.elgg_token,
            "__elgg_ts": self.elgg_user.elgg_ts,
            "body": reply_content,
            "parent_guid": wire_guid,
        }
        
        with self.client.post("/action/thewire/add", data=reply_data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Reply wire failed with status {response.status_code}")
    
    @task(5)
    def send_message(self):
        """Send a private message"""
        if not self.elgg_user.logged_in or not self.elgg_user.friends_list:
            return
        
        recipient_guid = random.choice(self.elgg_user.friends_list)
        message_content = RandomStringGenerator.generate_random_string(50, "alpha")
        message_subject = RandomStringGenerator.generate_random_string(10, "alpha")
        
        message_data = {
            "__elgg_token": self.elgg_user.elgg_token,
            "__elgg_ts": self.elgg_user.elgg_ts,
            "recipient_guid": recipient_guid,
            "subject": message_subject,
            "body": message_content,
        }
        
        with self.client.post("/action/messages/send", data=message_data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Send message failed with status {response.status_code}")
    
    @task(5)
    def read_message(self):
        """Read a received message"""
        if not self.elgg_user.logged_in or not self.elgg_user.messages_guids:
            return
        
        message_guid = random.choice(self.elgg_user.messages_guids)
        
        with self.client.get(f"/messages/read/{message_guid}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.extract_elgg_token_and_ts(response.text)
            else:
                response.failure(f"Read message failed with status {response.status_code}")
    
    @task(5)
    def sent_messages(self):
        """View sent messages"""
        if not self.elgg_user.logged_in:
            return
        
        with self.client.get(f"/messages/sent/{self.elgg_user.username}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.extract_elgg_token_and_ts(response.text)
            else:
                response.failure(f"Sent messages access failed with status {response.status_code}")
    
    @task(5)
    def delete_message(self):
        """Delete a message"""
        if not self.elgg_user.logged_in or not self.elgg_user.messages_guids:
            return
        
        message_guid = random.choice(self.elgg_user.messages_guids)
        
        delete_data = {
            "__elgg_token": self.elgg_user.elgg_token,
            "__elgg_ts": self.elgg_user.elgg_ts,
            "message_id[]": message_guid,
            "delete": "Delete",
        }
        
        with self.client.post("/action/messages/process/", data=delete_data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                if message_guid in self.elgg_user.messages_guids:
                    self.elgg_user.messages_guids.remove(message_guid)
            else:
                response.failure(f"Delete message failed with status {response.status_code}")
    
    @task(5)
    def check_blog(self):
        """Check blog posts"""
        if not self.elgg_user.logged_in:
            return
        
        blog_url = random.choice(["/blog", "/blog/owner/", "/blog/friends/"])
        
        with self.client.get(blog_url, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.extract_elgg_token_and_ts(response.text)
            else:
                response.failure(f"Check blog failed with status {response.status_code}")
    
    @task(5)
    def post_blog(self):
        """Post a blog entry"""
        if not self.elgg_user.logged_in:
            return
        
        blog_title = RandomStringGenerator.generate_random_string(20, "alpha")
        blog_content = RandomStringGenerator.generate_random_string(100, "alpha")
        
        blog_data = {
            "__elgg_token": self.elgg_user.elgg_token,
            "__elgg_ts": self.elgg_user.elgg_ts,
            "title": blog_title,
            "body": blog_content,
            "access": "1",
        }
        
        with self.client.post("/action/blog/save", data=blog_data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.extract_elgg_token_and_ts(response.text)
            else:
                response.failure(f"Post blog failed with status {response.status_code}")
    
    @task(0)
    def comment(self):
        """Comment on a blog"""
        if not self.elgg_user.logged_in or not self.elgg_user.blogs_guids:
            return
        
        blog_guid = random.choice(self.elgg_user.blogs_guids)
        comment_text = RandomStringGenerator.generate_random_string(15, "alpha")
        
        comment_data = {
            "__elgg_token": self.elgg_user.elgg_token,
            "__elgg_ts": self.elgg_user.elgg_ts,
            "generic_comment": comment_text,
            "entity_guid": blog_guid,
        }
        
        with self.client.post("/action/comment/save", data=comment_data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Comment failed with status {response.status_code}")
    
    @task(0)
    def do_like(self):
        """Like a blog or wire"""
        if not self.elgg_user.logged_in:
            return
        
        # Choose between blog or wire
        guids = self.elgg_user.blogs_guids + self.elgg_user.wires_guids
        if not guids:
            return
        
        target_guid = random.choice(guids)
        
        like_data = {
            "__elgg_token": self.elgg_user.elgg_token,
            "__elgg_ts": self.elgg_user.elgg_ts,
            "guid": target_guid,
        }
        
        with self.client.post("/action/likes/add", data=like_data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Like failed with status {response.status_code}")
    
    @task(2)
    def search(self):
        """Search for members"""
        if not self.elgg_user.logged_in:
            return
        
        search_query = self._get_random_user_name()
        if not search_query:
            return
        
        with self.client.get(f"/members/search?member_query={search_query}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.extract_elgg_token_and_ts(response.text)
            else:
                response.failure(f"Search failed with status {response.status_code}")
    
    # Helper methods
    def _get_random_user_guid(self) -> Optional[str]:
        """Get a random user GUID (different from current user)"""
        try:
            with open("/app/users.list", "r") as f:
                users = [line.strip().split(":") for line in f.readlines()]
                users = [u for u in users if len(u) >= 3 and u[2] != self.elgg_user.guid]
                if users:
                    return random.choice(users)[2]
        except Exception as e:
            logger.debug(f"Error getting random user GUID: {e}")
        return None
    
    def _get_random_user_name(self) -> Optional[str]:
        """Get a random username"""
        try:
            with open("/app/users.list", "r") as f:
                users = [line.strip().split(":")[0] for line in f.readlines()]
                if users:
                    return random.choice(users)
        except Exception as e:
            logger.debug(f"Error getting random user: {e}")
        return None


class ElggUserBehavior(HttpUser):
    """Main user class for Locust simulation"""
    
    tasks = [ElggBehavior]
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests


class FastElggUser(FastHttpUser):
    """High-performance user class using FastHttpUser"""
    
    tasks = [ElggBehavior]
    wait_time = between(1, 3)


# Event handlers for logging
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when a load test is started"""
    logger.info("Load test started")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when a load test is stopped"""
    logger.info("Load test stopped")
    logger.info(f"Total requests: {environment.stats.total.num_requests}")
    logger.info(f"Total failures: {environment.stats.total.num_failures}")
