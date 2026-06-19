# Advanced Configuration Guide for Elgg Locust Benchmark

## Workload Mix Customization

The original Faban benchmark used a `MatrixMix` to define different user types and behavior patterns. Here's how to replicate specific workload mixes in Locust:

### Original Faban Mix Analysis

The Web20Driver had 25 rows in the MatrixMix, representing different user profiles:

1. **Row 0**: 100% BrowsetoElgg (new arrivals)
2. **Row 1-2, 5-24**: Mixed workload (logged-in users)
3. **Row 3**: 100% BrowsetoElgg (casual browsers)
4. **Row 4**: 70% BrowsetoElgg, 30% Register (registration phase)

### Replicating in Locust

Create custom user classes for different behaviors:

```python
# In locustfile.py

from locust import HttpUser, between, task, TaskSet

class NewUserBehavior(TaskSet):
    """New users browsing Elgg"""
    @task(100)
    def browse_to_elgg(self):
        self.client.get("/")

class NewUserClass(HttpUser):
    tasks = [NewUserBehavior]
    wait_time = between(2, 5)

class ActiveUserBehavior(TaskSet):
    """Active users with mixed workload"""
    @task(5)
    def add_friend(self):
        # ... friend request
        pass
    
    @task(5)
    def post_wire(self):
        # ... post wire
        pass
    
    @task(5)
    def send_message(self):
        # ... send message
        pass
    
    # ... other operations

class ActiveUserClass(HttpUser):
    tasks = [ActiveUserBehavior]
    wait_time = between(1, 2)
```

## Performance Tuning

### 1. Adjusting Think Time

Locust's `wait_time` controls the delay between requests:

```python
# Constant think time (e.g., 2 seconds)
from locust import constant
wait_time = constant(2)

# Random think time (1-3 seconds)
from locust import between
wait_time = between(1, 3)

# Exponential think time (realistic user behavior)
from locust import constant_pacing
wait_time = constant_pacing(2)  # Total cycle time = 2 seconds

# Custom function
def think_time():
    return random.gauss(2, 0.5)  # Normal distribution

wait_time = think_time
```

### 2. Connection Pooling

Locust automatically pools HTTP connections. To tune:

```python
class ElggUserBehavior(HttpUser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adjust connection pool size
        self.client.pool_connections = 5
        self.client.pool_maxsize = 10
```

### 3. FastHttpUser for Higher Throughput

```python
from locust.contrib.fasthttp import FastHttpUser

class FastElggUser(FastHttpUser):
    tasks = [ElggBehavior]
    wait_time = between(1, 2)
```

## Token and Session Management

### Automatic CSRF Token Extraction

The default implementation extracts tokens from JSON responses:

```python
def extract_elgg_token_and_ts(self, response_text: str):
    """Extract Elgg security tokens"""
    token_match = re.search(r'"__elgg_token":"([^"]+)"', response_text)
    ts_match = re.search(r'"__elgg_ts":(\d+)', response_text)
    return token_match.group(1), ts_match.group(1)
```

### Session Persistence

Locust automatically manages cookies for session persistence. To clear sessions:

```python
def on_start(self):
    """Called when user session starts"""
    self.client.cookies.clear()
    # Then perform login
    self.login()

def on_stop(self):
    """Called when user session stops"""
    self.logout()
```

## Metrics and Monitoring

### Custom Metrics

Add custom metrics to track specific behaviors:

```python
from locust.env import Environment
from locust import events

@events.request.add_listener
def request_handler(request_type, name, response_time, response_length, 
                   response, context, exception, **kwargs):
    if exception:
        print(f"Request failed: {name}")
    elif response_time > 1000:
        print(f"Slow request: {name} took {response_time}ms")
```

### CSV Export

Results are automatically exported to CSV. Customize with:

```bash
locust -f locustfile.py \
  --csv=results \
  --csv-prefix=benchmark_run_1
```

This creates:
- `benchmark_run_1_stats.csv`
- `benchmark_run_1_stats_history.csv`
- `benchmark_run_1_failures.csv`

## Distributed Testing Configuration

### Master Node Optimization

```bash
locust -f locustfile.py \
  --master \
  --master-bind-host 0.0.0.0 \
  --master-bind-port 5557 \
  --expect-workers 4 \
  --headless \
  --users 1000 \
  --spawn-rate 50 \
  --run-time 10m
```

### Worker Node Configuration

```bash
locust -f locustfile.py \
  --worker \
  --master-host master-ip \
  --master-port 5557 \
  --worker-loglevel info
```

### Multiple Workers on Same Machine

```python
# Use multiprocessing for multiple worker processes
import multiprocessing
num_processes = multiprocessing.cpu_count()
```

## Docker Deployment

### Production Docker Compose

```yaml
version: '3.8'

services:
  locust-master:
    image: elgg-locust
    ports:
      - "8089:8089"
    command: >
      locust -f locustfile.py
        --master
        --master-bind-host 0.0.0.0
        --expect-workers 3
        --headless
        --users 500
        --spawn-rate 25
        --run-time 30m

  locust-worker-1:
    image: elgg-locust
    command: >
      locust -f locustfile.py
        --worker
        --master-host locust-master
    depends_on:
      - locust-master

  locust-worker-2:
    image: elgg-locust
    command: >
      locust -f locustfile.py
        --worker
        --master-host locust-master
    depends_on:
      - locust-master

  locust-worker-3:
    image: elgg-locust
    command: >
      locust -f locustfile.py
        --worker
        --master-host locust-master
    depends_on:
      - locust-master
```

## Debugging and Logging

### Enable Debug Logging

```bash
locust -f locustfile.py \
  --loglevel DEBUG \
  --logfile locust.log
```

### Request Logging

```python
import logging

class ElggBehavior(TaskSet):
    def on_start(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @task
    def some_operation(self):
        self.logger.info(f"User {self.client} executing operation")
```

### Exception Handling

```python
@task
def operation_with_error_handling(self):
    try:
        response = self.client.get("/some-endpoint")
        if response.status_code != 200:
            self.logger.error(f"Got status {response.status_code}")
    except Exception as e:
        self.logger.exception(f"Operation failed: {e}")
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Load Test

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  load-test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      
      - name: Install dependencies
        run: |
          pip install -r benchmarks/web-serving/locust_client/requirements.txt
      
      - name: Run load test
        run: |
          cd benchmarks/web-serving/locust_client
          locust -f locustfile.py \
            --host http://staging.elgg.local \
            --users 100 \
            --spawn-rate 10 \
            --run-time 5m \
            --headless \
            --csv=results
      
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: load-test-results
          path: benchmarks/web-serving/locust_client/results*.csv
```

## Performance Analysis

### Interpreting Results

1. **Baseline Establishment**
   - Run test against known good state
   - Record: RPS, avg response time, 95th percentile, failures

2. **Regression Detection**
   - Run same test after code changes
   - Compare metrics to baseline
   - Flag significant deviations

3. **Capacity Planning**
   - Test with increasing load
   - Identify breaking point
   - Calculate capacity headroom

## Advanced Customization Examples

### Custom Task Selection

```python
class ElggBehavior(TaskSet):
    tasks = {
        login: 10,           # 10% login
        browse: 40,          # 40% browsing
        post_content: 30,    # 30% content creation
        search: 20,          # 20% search
    }
```

### Conditional Task Execution

```python
@task(5)
def add_friend(self):
    if self.user.logged_in:
        # ... execute
    else:
        # Skip this operation
        pass
```

### Dynamic User State

```python
def on_start(self):
    self.user.credits = 100
    self.user.reputation = 0

@task
def spend_credits(self):
    if self.user.credits > 0:
        self.user.credits -= 10
        # ... execute operation
```

## References

- [Locust Documentation](https://docs.locust.io/)
- [HTTP User Docs](https://docs.locust.io/en/stable/api.html#http-user)
- [Wait Time Documentation](https://docs.locust.io/en/stable/api.html#wait_time)
- [Distributed Testing](https://docs.locust.io/en/stable/running-locust-distributed.html)
- [FastHTTP User](https://docs.locust.io/en/stable/api.html#fasthttp-user)
