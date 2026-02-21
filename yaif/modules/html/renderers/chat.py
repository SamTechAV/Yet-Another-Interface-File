"""
yaif/modules/html/renderers/chat.py

Renders a [page type: chat] into an HTML <section>.

Page props
----------
title           Page heading
subtitle        Optional subheading
placeholder     Input placeholder text (default "Type a message...")
send            Send button label (default "Send")

[message]
  author    Display name of the sender
  text      Message body (supports line breaks via \\n)
  side      left | right  (default left)
  time      Timestamp string e.g. "2:41 PM"
  avatar    Single char or emoji used as avatar fallback  e.g. "A" or "🤖"
"""

from __future__ import annotations
import html as _h


def _esc(s) -> str:
    return _h.escape(str(s)) if s is not None else ''


def _avatar_colour(name: str) -> str:
    """Deterministic muted colour from author name."""
    colours = [
        '#7c6f9f', '#6f8fa8', '#8fa86f', '#a88f6f',
        '#a86f8f', '#6fa8a0', '#a0a86f', '#8f6fa8',
    ]
    idx = sum(ord(c) for c in name) % len(colours)
    return colours[idx]


def _render_message(msg: dict) -> str:
    author = str(msg.get('author', 'Unknown'))
    text   = _esc(str(msg.get('text', ''))).replace('\\n', '<br>')
    side   = str(msg.get('side', 'left')).lower()
    time   = _esc(str(msg.get('time', '')))
    avatar = _esc(str(msg.get('avatar', author[0].upper() if author else '?')))

    side_cls     = 'msg-right' if side == 'right' else 'msg-left'
    bubble_cls   = 'bubble-right' if side == 'right' else 'bubble-left'
    av_colour    = _avatar_colour(author)
    av_style     = f'style="background:{av_colour}"'

    time_html = f'<span class="msg-time">{time}</span>' if time else ''

    return f'''
      <div class="message {side_cls}">
        <div class="avatar" {av_style} aria-label="{_esc(author)}">{avatar}</div>
        <div class="msg-body">
          <div class="msg-meta">
            <span class="msg-author">{_esc(author)}</span>
            {time_html}
          </div>
          <div class="bubble {bubble_cls}">{text}</div>
        </div>
      </div>'''


def render(page: dict) -> str:
    props       = page.get('props', {})
    title       = _esc(props.get('title', page['name'].replace('_', ' ')))
    subtitle    = _esc(props.get('subtitle', ''))
    placeholder = _esc(props.get('placeholder', 'Type a message...'))
    send_label  = _esc(props.get('send', 'Send'))
    messages    = page.get('messages', [])

    messages_html = ''.join(_render_message(m) for m in messages)

    if not messages_html:
        messages_html = '<p class="empty-state">No messages yet.</p>'

    return f'''
  <section class="page page-chat" id="page-{_esc(page['name'])}">
    <div class="page-header">
      <div>
        <h2 class="page-title">{title}</h2>
        {f'<p class="page-sub">{subtitle}</p>' if subtitle else ''}
      </div>
    </div>
    <div class="chat-window">
      <div class="messages">
        {messages_html}
      </div>
      <div class="chat-input-bar">
        <input type="text" class="chat-input" placeholder="{placeholder}" aria-label="{placeholder}">
        <button class="btn-primary chat-send">{send_label}</button>
      </div>
    </div>
  </section>'''