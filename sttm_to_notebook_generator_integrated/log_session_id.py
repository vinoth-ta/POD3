import time

def generate_unique_ID():
    from datetime import datetime, timezone
    import uuid

    # Get current UTC time
    utc_now = datetime.now(timezone.utc)
    # Convert to epoch in milliseconds
    epoch_ms = int(utc_now.timestamp() * 1000)
    # Generate a random GUID (UUID v4)
    guid = str(uuid.uuid4())
    unique_ID=f"{epoch_ms}-{guid}"

    return(unique_ID)
    


# This gets set ONCE at app startup
SESSION_LOG_ID = str(time.time_ns())+"-"+generate_unique_ID()