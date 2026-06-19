# Locust-based Elgg Benchmark Load Generator

This is a modern replacement for the Faban-based `Web20Driver.java` load generator. It uses Locust, a Python-based load testing framework, to simulate realistic user behavior on an Elgg social network.

## Overview

The Locust load generator simulates 25 different user operations:

- **Authentication**: Login, Register, Logout
- **Social Features**: Add Friend, Remove Friend, Check Friends
- **Activity**: Check Activity, Dashboard, Access Home Page
- **Notifications**: Get Notifications, Inbox, Sent Messages
- **Messaging**: Send Message, Read Message, Delete Message
- **Content**: Check Profile, Check Blog, Post Blog, Comment
- **Wires**: Check Wire, Post Wire, Reply Wire
- **Interactions**: Like, Search
- **Browse**: Browse to Elgg

## Advantages over Faban

- **Modern**: Locust is actively maintained and widely used for load testing
- **Python-based**: Easy to understand, modify, and extend
- **Distributed**: Native support for distributed testing across multiple machines
- **Web UI**: Real-time monitoring and control dashboard
- **Flexible**: Support for custom logic, hooks, and metrics
- **Lower overhead**: More efficient than Faban for generating load

## Installation

### Local Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Docker Installation

```bash
# Build the Docker image
docker build -t elgg-locust .
```

## Usage

### 1. Web UI Mode (Interactive)

```bash
locust -f locustfile.py --host http://elgg-server:8080
```

Then open your browser to `http://localhost:8089` and:
1. Enter the number of users to simulate
2. Enter the spawn rate (users per second)
3. Click "Start swarming"

### 2. Headless Mode (Scripted)

```bash
# Run for 5 minutes with 100 users
locust -f locustfile.py \
  --host http://elgg-server:8080 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless
```

### 3. Distributed Testing

**On Master Node:**
```bash
locust -f locustfile.py \
  --host http://elgg-server:8080 \
  --master \
  --master-bind-host 0.0.0.0 \
  --master-bind-port 5557
```

**On Worker Node(s):**
```bash
locust -f locustfile.py \
  --host http://elgg-server:8080 \
  --worker \
  --master-host master-node-ip \
  --master-port 5557
```

### 4. Docker Container

```bash
# Single container
docker run -p 8089:8089 \
  -e LOCUST_HOST=http://elgg-server:8080 \
  elgg-locust

# With command line options
docker run -p 8089:8089 \
  elgg-locust \
  locust -f locustfile.py \
    --host http://elgg-server:8080 \
    --users 50 \
    --spawn-rate 5 \
    --headless
```

## Configuration

### Users List

Edit `users.list` to add test users:

```
username:password:guid
user1:pass1:1
user2:pass2:2
```

Format: `username:password:guid` (colon-separated)

### Load Pattern Customization

Modify the `@task()` decorator values in `locustfile.py` to adjust operation frequencies:

```python
@task(100)  # Higher number = more frequent
def browse_to_elgg(self):
    ...

@task(5)    # Lower number = less frequent
def add_friend(self):
    ...

@task(0)    # 0 = disabled
def comment(self):
    ...
```

The numbers represent relative weights, so `@task(100)` occurs twice as often as `@task(50)`.

### Think Time

Adjust the wait time between requests:

```python
class ElggUserBehavior(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
```

## Monitoring

### Web UI Dashboard

When running with the web UI, access the dashboard at `http://localhost:8089`:

- **Statistics**: Real-time request counts, response times, failure rates
- **Charts**: Response time distribution, requests/second over time
- **Failures**: Details of any failed requests
- **System**: Current user count, spawn rate

### Command Line Output

In headless mode, Locust prints summary statistics:

```
Name                     | requests | fails | avg (ms) | min (ms) | max (ms) | median (ms) | 95% (ms) | 99% (ms)
```

## Comparison with Faban

| Feature | Faban | Locust |
|---------|-------|--------|
| Language | Java | Python |
| Learning Curve | Steep | Gentle |
| Distributed | Complex setup | Built-in |
| Real-time Dashboard | Limited | Excellent |
| Extensibility | Moderate | Excellent |
| Maintenance | Legacy | Active |
| Memory Footprint | High | Low |

## Performance Tips

1. **Use FastHttpUser** instead of HttpUser for high throughput:
   ```python
   from locustfile import FastElggUser
   # Then set host to use FastElggUser
   ```

2. **Tune Worker Count** for distributed testing:
   - Start with 1 worker per CPU core
   - Monitor master-worker communication latency

3. **Increase spawn rate gradually** to avoid overwhelming the server

4. **Monitor the target system's resources** (CPU, memory, network)

5. **Use headless mode** in production for lower overhead

## Troubleshooting

### Connection Refused

- Ensure the target Elgg server is running and accessible
- Check the `--host` parameter
- Verify firewall rules

### High Failure Rate

- Check Elgg server logs for errors
- Verify user credentials in `users.list`
- Reduce spawn rate or user count
- Check network connectivity

### Token Extraction Errors

- Ensure the Elgg token extraction regex matches your server version
- Check Elgg server's HTML response format
- Review logs for specific errors

## Customization Examples

### Add Custom User Behavior

```python
@task(2)
def custom_operation(self):
    with self.client.get("/custom-endpoint", catch_response=True) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"Failed: {response.status_code}")
```

### Add Custom Metrics

```python
from locust.env import Environment
from locust.stats import StatsEntry

# In your operation:
if "special_condition" in response.text:
    # Track custom metric
    pass
```

### Custom User Lifecycle

```python
def on_start(self):
    """Called when user starts"""
    self.setup_user()
    self.do_login()

def on_stop(self):
    """Called when user stops"""
    self.logout()
```

## References

- [Locust Documentation](https://locust.io/)
- [Locust API Reference](https://docs.locust.io/en/stable/api.html)
- [Distributed Load Testing](https://docs.locust.io/en/stable/running-locust-distributed.html)

## Migration from Faban

If you were using the Faban `Web20Driver.java`:

1. **Operations** - All 25 operations have been ported
2. **User Management** - Same `users.list` format supported
3. **CSRF Tokens** - Automatically extracted from responses
4. **Workload Mix** - Can be replicated with Locust task weights
5. **Metrics** - Available in web UI and CSV export

## License

This load generator is based on the original Faban-based Web20Driver by Tapti Palit and Ali Ansari, adapted for Locust.
