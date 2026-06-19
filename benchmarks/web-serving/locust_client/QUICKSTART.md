# Quick Start Guide - Locust Elgg Benchmark

## Installation (5 minutes)

### Option 1: Local Installation

```bash
# Navigate to the locust client directory
cd benchmarks/web-serving/locust_client

# Install Python dependencies
pip install -r requirements.txt
```

### Option 2: Docker

```bash
cd benchmarks/web-serving/locust_client

# Build the Docker image
docker build -t elgg-locust .
```

## Running the Load Test

### Option 1: Web UI Mode (Easiest)

```bash
# Start Locust with web interface
./run_locust.sh ui --host http://your-elgg-server:8080
```

Then:
1. Open http://localhost:8089 in your browser
2. Enter the number of users (e.g., 50)
3. Enter spawn rate (e.g., 5 users/second)
4. Click "Start swarming"
5. Watch real-time statistics and graphs

### Option 2: Headless Mode (Scripted)

```bash
# Run for 5 minutes with 100 users
./run_locust.sh headless \
  --host http://your-elgg-server:8080 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m
```

### Option 3: Docker

```bash
# Single run
docker run -p 8089:8089 \
  -e LOCUST_HOST=http://your-elgg-server:8080 \
  elgg-locust

# Or with docker-compose
cd benchmarks/web-serving/locust_client
docker-compose up
```

## Configuration

### Edit Users

Modify `users.list` with your test user accounts:

```
username:password:guid
admin:adminpass:1
user1:pass1:2
user2:pass2:3
```

### Adjust Workload Mix

Edit `locustfile.py` to change operation frequencies:

```python
@task(100)  # Highly frequent
def browse_to_elgg(self):
    ...

@task(5)    # Less frequent
def add_friend(self):
    ...

@task(0)    # Disabled
def comment(self):
    ...
```

### Modify Think Time

Change wait time between requests in `locustfile.py`:

```python
class ElggUserBehavior(HttpUser):
    wait_time = between(1, 3)  # Change these numbers
```

## Understanding Results

### Key Metrics

| Metric | Meaning |
|--------|---------|
| Requests/s | Throughput - requests per second |
| Response Time (avg) | Average response time in milliseconds |
| 95% (95th percentile) | 95% of requests completed within this time |
| Failures | Number of failed requests |
| RPS | Requests per second |

### In Web UI

- **Statistics Tab**: Detailed per-endpoint metrics
- **Charts Tab**: Real-time graphs of response times and RPS
- **Failures Tab**: Details of any failed requests
- **System Tab**: Current user count and test metrics

## Advanced Usage

### Distributed Testing (Multiple Machines)

**Machine 1 (Master):**
```bash
./run_locust.sh master --host http://elgg-server:8080
```

**Machine 2-N (Workers):**
```bash
./run_locust.sh worker \
  --host http://elgg-server:8080 \
  # When prompted, enter master machine IP
```

### Export Results

Results are automatically saved to CSV files with prefix "results_":

```
results_stats.csv       # Per-endpoint statistics
results_stats_history.csv # Statistics over time
results_failures.csv    # Failed requests
```

### Custom Configuration

Use the `locust.conf` file for common settings:

```bash
locust -f locustfile.py --config locust.conf
```

## Troubleshooting

### "Connection refused"
- Check that Elgg server is running
- Verify the host URL is correct
- Check firewall rules

### "High failure rate"
- Ensure users exist in `users.list`
- Check credentials are correct
- Reduce the spawn rate
- Review Elgg server logs

### "Token extraction failed"
- Verify Elgg server is the expected version
- Check that HTML response format hasn't changed
- Review debug logs for parsing errors

## Performance Considerations

- **Use FastHttpUser** for higher throughput
- **Increase workers** for distributed load
- **Reduce spawn rate** if server is overloaded
- **Monitor target system** resources during test
- **Start small** (10-50 users) then scale up

## Next Steps

1. **Read the full README.md** for comprehensive documentation
2. **Customize operations** in locustfile.py for your needs
3. **Set up monitoring** on target server
4. **Run baseline tests** to establish performance baseline
5. **Use in CI/CD pipeline** for regression testing

For more info, see: https://locust.io/
