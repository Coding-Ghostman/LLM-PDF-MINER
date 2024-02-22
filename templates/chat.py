css = '''
<style>
    .chat-container {
        max-width: 600px;
        margin: 0 auto;
    }

    .chat-message {
        display: flex;
        margin-bottom: 1rem;
        align-items: flex-start;
    }

    .avatar {
        flex-shrink: 0;
        margin-right: 1rem;
    }

    .avatar img {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        object-fit: cover;
    }

    .message-container {
        background-color: #f0f0f0;
        padding: 1rem;
        border-radius: 0.5rem;
        flex-grow: 1;
    }

    .user .message-container {
        background-color: #2b313e;
        color: #fff;
    }

    .bot .message-container {
        background-color: #475063;
        color: #fff;
    }
</style>
'''

bot_template = '''
<div class="chat-message bot">
    <div class="avatar">
        <img src="https://i.ibb.co/cN0nmSj/Screenshot-2023-05-28-at-02-37-21.png">
    </div>
    <div class="message-container">{{MSG}}</div>
</div>
'''

user_template = '''
<div class="chat-message user">
    <div class="avatar">
        <img src="https://i.ibb.co/rdZC7LZ/Photo-logo-1.png">
    </div>
    <div class="message-container">{{MSG}}</div>
</div>
'''
