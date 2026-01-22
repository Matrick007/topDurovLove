from utils import create_user, create_channel, add_user_to_channel

# Create user
user_id = create_user('testuser', '123456')
print(f"Created user with id: {user_id}")

# Create channel
channel_id = create_channel('testchannel', 'testuser')
print(f"Created channel with id: {channel_id}")

# Add user to channel
add_user_to_channel(channel_id, user_id)
print("Added user to channel")