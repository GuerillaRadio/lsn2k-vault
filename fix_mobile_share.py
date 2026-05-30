content = open('templates/index.html', encoding='utf-8').read()

# ── 1. Share button CSS ───────────────────────────────────────────────────
share_css = """
    .msg-actions{
      display:flex;justify-content:flex-end;margin-top:6px;opacity:0;
      transition:opacity .15s;
    }
    .msg:hover .msg-actions{ opacity:1; }
    /* always visible on touch devices */
    @media(hover:none){ .msg-actions{ opacity:1; } }
    .share-btn{
      background:none;border:1px solid var(--border);color:var(--dim);
      font-family:"Oswald",sans-serif;font-size:.62rem;letter-spacing:1px;
      text-transform:uppercase;padding:4px 10px;border-radius:3px;cursor:pointer;
      display:flex;align-items:center;gap:5px;transition:.15s;
    }
    .share-btn:hover{ border-color:var(--gold);color:var(--gold); }
    .share-btn.copied{ border-color:#4caf50;color:#4caf50; }
    .share-btn svg{ width:11px;height:11px; }

    /* ── Mobile layout ── */
    @media(max-width:640px){
      header{ padding:8px 14px; }
      .brand img{ height:34px; }
      .brand h1{ font-size:1rem; }
      .brand .sub{ display:none; }
      .szn-pill{ display:none; }
      #reset-btn{ padding:5px 10px;font-size:.65rem; }

      #landing{ padding:16px 14px 12px;gap:0; }
      .logo-hero{ width:min(280px,80vw);margin-bottom:20px; }
      .coach-row{ gap:12px;max-width:100%; }
      .coach-face{ width:60px; }
      .coach-copy h2{ font-size:1.1rem; }
      .coach-copy p{ font-size:.8rem;margin-top:5px; }

      #suggestions{
        grid-template-columns:1fr;gap:7px;margin-top:18px;
        max-height:38vh;overflow-y:auto;
      }
      .suggestion{ padding:10px 12px;font-size:.82rem; }
      .suggestion .cat{ width:46px;font-size:.58rem; }

      #chat-wrap{ padding:16px 0 4px;gap:16px; }
      .msg{ padding:0 12px;gap:8px; }
      .avatar{ width:34px; }
      .user-avatar{ width:28px;height:28px;font-size:.6rem; }
      .msg-col{ max-width:calc(100% - 42px); }
      .nameplate{ font-size:.64rem; }
      .bubble{ padding:11px 13px;font-size:.87rem;line-height:1.7; }
      .bubble table{ font-size:.78rem; }
      .bubble thead th{ padding:7px 9px;font-size:.66rem; }
      .bubble tbody td{ padding:7px 9px;font-size:.76rem; }

      #input-area{ padding:10px 12px 14px; }
      #input-row{ gap:8px; }
      #user-input{ font-size:.88rem;padding:10px 12px;border-radius:10px; }
      #send-btn{ width:42px;height:42px; }
      #status{ font-size:.62rem; }

      .coach-status-text{ font-size:.8rem; }
      .bubble.status-mode{ min-width:160px; }
    }
"""

# Insert share CSS before closing </style>
content = content.replace('  </style>', share_css + '  </style>')

# ── 2. Share button JS + inject into addMessage ──────────────────────────
share_js = """
function copyResponse(btn, text) {
  // Strip markdown-ish syntax for clean copy
  const clean = text
    .replace(/\\*\\*(.*?)\\*\\*/g, '$1')
    .replace(/\\*(.*?)\\*/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/^#+\\s+/gm, '')
    .replace(/^[-•]\\s+/gm, '• ')
    .trim();
  navigator.clipboard.writeText(clean).then(() => {
    btn.classList.add('copied');
    btn.querySelector('.share-label').textContent = 'Copied!';
    setTimeout(() => {
      btn.classList.remove('copied');
      btn.querySelector('.share-label').textContent = 'Share';
    }, 2000);
  });
}
"""

# Add share JS before closing </script>
content = content.replace('</script>', share_js + '\n</script>')

# ── 3. Add share button to assistant messages in addMessage ──────────────
old_append = """  col.appendChild(bubble);
  div.appendChild(avatar);
  div.appendChild(col);
  chatWrap.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}"""

new_append = """  col.appendChild(bubble);

  // Share button for assistant messages
  if (role === 'assistant') {
    const actions = document.createElement('div');
    actions.className = 'msg-actions';
    const shareBtn = document.createElement('button');
    shareBtn.className = 'share-btn';
    const rawText = typeof content === 'string' ? content :
      (Array.isArray(content) ? content.filter(b=>b.type==='text').map(b=>b.text).join('\\n') : '');
    shareBtn.onclick = () => copyResponse(shareBtn, rawText);
    shareBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg><span class="share-label">Share</span>`;
    actions.appendChild(shareBtn);
    col.appendChild(actions);
  }

  div.appendChild(avatar);
  div.appendChild(col);
  chatWrap.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}"""

content = content.replace(old_append, new_append)

open('templates/index.html', 'w', encoding='utf-8').write(content)
print("done")
