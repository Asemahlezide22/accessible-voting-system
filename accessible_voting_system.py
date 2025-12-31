import os, sys, json, uuid
from django.conf import settings
from django.core.management import execute_from_command_line
from django.http import HttpResponse, JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.core.wsgi import get_wsgi_application

# ============================================
# DJANGO SETTINGS
# ============================================
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='django-insecure-key-12345',
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=['*'],
        MIDDLEWARE=['django.middleware.common.CommonMiddleware'],
        INSTALLED_APPS=['django.contrib.staticfiles'],
        TEMPLATES=[{'BACKEND': 'django.template.backends.django.DjangoTemplates'}],
        STATIC_URL='/static/',
    )

# ============================================
# PERSISTENT DATA STORAGE 
# ============================================
DATA_FILE = 'voting_data.json'

def load_data():
    """Load data from file - keeps votes between runs"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                print(f"✅ Loaded data: {sum(data.get('VOTE_COUNT', {}).values())} total votes")
                return data
        except:
            pass
    return {
        'VOTE_COUNT': {str(i): 0 for i in range(1, 6)},
        'VOTERS': {str(i): [] for i in range(1, 6)},
        'SURVEY_RESPONSES': [],
        'VALID_TOKENS': {}
    }

def save_data():
    """Save data to file - PERMANENT STORAGE!"""
    data = {
        'VOTE_COUNT': {str(k): v for k, v in VOTE_COUNT.items()},
        'VOTERS': {str(k): v for k, v in VOTERS.items()},
        'SURVEY_RESPONSES': SURVEY_RESPONSES,
        'VALID_TOKENS': VALID_TOKENS
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"💾 Saved! Total votes: {sum(VOTE_COUNT.values())}")

# Load existing data
saved_data = load_data()

CANDIDATES = {
    1: 'Accessible Transport',
    2: 'Inclusive Education',
    3: 'Assistive Technology',
    4: 'Healthcare Accessibility',
    5: 'Digital Inclusion'
}

VOTE_COUNT = {int(k): v for k, v in saved_data.get('VOTE_COUNT', {}).items()}
VOTERS = {int(k): v for k, v in saved_data.get('VOTERS', {}).items()}
SURVEY_RESPONSES = saved_data.get('SURVEY_RESPONSES', [])
CURRENT_USER = None
VALID_TOKENS = saved_data.get('VALID_TOKENS', {})

SURVEY_QUESTIONS = [
    "Are schools accessible for students with disabilities?",
    "Do workplaces provide reasonable accommodations?",
    "Is public transport disability-friendly?",
    "Do you have access to assistive technology?",
    "Are healthcare facilities inclusive?",
    "Do you feel represented in policy-making?",
    "Are emergency services accessible?",
    "Do you have access to digital accessibility tools?",
    "Is voting easy for people with disabilities?",
    "Would you recommend improvements in accessibility laws?"
]
OPTIONS = ["Yes", "No", "Partially"]

def get_response(question):
    """AI chatbot responses"""
    q = question.lower()
    if any(w in q for w in ['vote', 'result', 'winning']):
        total = sum(VOTE_COUNT.values())
        if total == 0:
            return "📊 No votes yet!"
        winner = max(VOTE_COUNT, key=VOTE_COUNT.get)
        resp = f"🏆 Leading: {CANDIDATES[winner]} ({VOTE_COUNT[winner]} votes)\n\n"
        for cid, name in CANDIDATES.items():
            v = VOTE_COUNT[cid]
            pct = (v/total)*100 if total > 0 else 0
            resp += f"• {name}: {v} votes ({pct:.1f}%)\n"
        return resp
    if 'survey' in q:
        return f"📋 Survey responses: {len(SURVEY_RESPONSES)}"
    return "Ask about voting results or surveys!"

# ============================================
# ACCESSIBILITY TOOLBAR - ON ALL PAGES
# ============================================
TOOLBAR = """
<div class="toolbar">
<button onclick="changeSize(-2)" title="Decrease text">A-</button>
<button onclick="changeSize(2)" title="Increase text">A+</button>
<button onclick="toggleContrast()" title="High contrast">🎨</button>
<button onclick="toggleVoice()" id="vBtn" title="Voice reader">🔊</button>
<button onclick="voiceVote()" title="Vote by voice" style="background:#28a745">🎤 Voice</button>
</div>
<script>
let size=16,contrast=false,voice=false;
function changeSize(d){
    size=Math.max(12,Math.min(24,size+d));
    document.body.style.fontSize=size+'px';
    document.querySelectorAll('*').forEach(el => {
        if(el.style.fontSize) {
            const currentSize = parseFloat(getComputedStyle(el).fontSize);
            el.style.fontSize = (currentSize + d) + 'px';
        }
    });
    speak('Text size '+(d>0?'increased':'decreased'));
}
function toggleContrast(){
    contrast=!contrast;
    if(contrast) {
        document.body.style.filter='contrast(1.8) brightness(1.2)';
        document.body.style.background='#000';
    } else {
        document.body.style.filter='';
        document.body.style.background='';
    }
    speak(contrast?'High contrast on':'High contrast off');
}
function toggleVoice(){
    voice=!voice;
    document.getElementById('vBtn').style.background=voice?'#28a745':'';
    speak(voice?'Voice enabled':'Voice disabled');
}
function speak(t){
    if(voice&&'speechSynthesis' in window){
        const u=new SpeechSynthesisUtterance(t);
        u.rate=1;
        speechSynthesis.speak(u);
    }
}
function voiceVote(){
    if(!('webkitSpeechRecognition' in window)){
        alert('Voice not supported. Use Chrome!');
        return;
    }
    const r=new webkitSpeechRecognition();
    r.lang='en-US';
    r.continuous=false;
    speak('Say 1 for Transport, 2 for Education, 3 for Technology, 4 for Healthcare, 5 for Digital');
    r.onresult=function(e){
        const t=e.results[0][0].transcript.toLowerCase();
        let c=null;
        if(t.includes('one')||t.includes('1')||t.includes('transport'))c=1;
        else if(t.includes('two')||t.includes('2')||t.includes('education'))c=2;
        else if(t.includes('three')||t.includes('3')||t.includes('tech'))c=3;
        else if(t.includes('four')||t.includes('4')||t.includes('health'))c=4;
        else if(t.includes('five')||t.includes('5')||t.includes('digital'))c=5;
        if(c){
            speak('Voting for option '+c);
            if(typeof submitVote!=='undefined')submitVote(c);
        } else {
            speak('Sorry, try again');
        }
    };
    r.onerror=()=>speak('Error, try again');
    r.start();
}
</script>
"""

# ============================================
# PAGE VIEWS
# ============================================

def welcome(request):
    return HttpResponse("""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Accessible Voting</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#0a66c2 0%,#004182 50%,#002855 100%);height:100vh;overflow:hidden;font-size:16px}
.toolbar{background:#000;padding:0.5rem;display:flex;justify-content:center;gap:0.5rem;flex-wrap:wrap}
.toolbar button{padding:0.4rem 0.8rem;background:#333;color:#fff;border:1px solid #fff;border-radius:4px;cursor:pointer;font-size:0.85rem}
.toolbar button:hover{background:#fff;color:#000}
.header{background:#000;color:#fff;padding:0.5rem;text-align:center}
.header h1{font-size:1.2rem}
.container{max-width:1100px;margin:0.3rem auto;padding:0.3rem;height:calc(100vh - 120px);overflow:hidden;display:flex;align-items:center;justify-content:center}
.hero{background:#fff;padding:1.2rem 1.5rem;border-radius:12px;text-align:center;box-shadow:0 10px 30px rgba(0,0,0,0.2);width:100%;max-height:100%;overflow:hidden}
.hero p{font-size:0.85rem;color:#718096;margin-bottom:0.5rem}
.hero-img{max-width:100%;width:750px;height:auto;max-height:380px;object-fit:contain;border-radius:12px;margin:0.5rem auto;box-shadow:0 8px 20px rgba(10,102,194,0.2);display:block}
.btn{padding:0.7rem 1.5rem;background:linear-gradient(135deg,#0a66c2 0%,#004182 100%);color:#fff;border:none;border-radius:8px;font-size:0.95rem;cursor:pointer;text-decoration:none;display:inline-block}
.btn:hover{transform:translateY(-2px)}
</style>
</head>
<body>
""" + TOOLBAR + """
<div class="header"><h1>Accessible Voting & Survey System</h1></div>
<div class="container">
<div class="hero">
<h1 style="font-size:1.6rem;font-weight:700;color:#0a66c2;margin-bottom:0.2rem">🌟 Breaking Barriers, Building Futures</h1>
<h2 style="font-size:1rem;font-weight:600;color:#004182;margin-bottom:0.3rem">Your Voice Shapes Accessible Communities</h2>
<p style="font-size:0.8rem;color:#718096;margin-bottom:0.5rem">Empowering voices for disability accessibility</p>
<img src="/images/collage.jpg" alt="Accessibility" class="hero-img">
<h3 style="font-size:0.95rem;font-weight:600;color:#0a66c2;margin:0.5rem 0">✨ Join the Movement</h3>
<a href="/signin/" class="btn">Sign In to Participate</a>
<p style="margin-top:0.5rem;color:#718096;font-size:0.75rem">🤝 Join thousands making a difference</p>
</div>
</div>
</body>
</html>
    """)

@csrf_exempt
def login(request):
    global CURRENT_USER
    if request.method == 'POST':
        u = request.POST.get('username', '').strip()
        p = request.POST.get('password', '').strip()
        if len(u) >= 4 and len(p) >= 4:
            CURRENT_USER = u
            token = str(uuid.uuid4())
            VALID_TOKENS[token] = u
            save_data()
            return HttpResponse(f"<script>localStorage.setItem('auth_token','{token}');window.location.href='/app/';</script>")
    
    return HttpResponse("""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Sign In</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#0a66c2,#004182,#002855);min-height:100vh;display:flex;align-items:center;justify-content:center}
.box{background:#fff;padding:3rem;border-radius:16px;max-width:450px;width:90%}
.box h2{text-align:center;color:#0a66c2;margin-bottom:2rem}
.group{margin-bottom:1.5rem}
.group label{display:block;margin-bottom:0.5rem;font-weight:600}
.group input{width:100%;padding:0.8rem;border:2px solid #e2e8f0;border-radius:8px;font-size:1rem}
.btn{width:100%;padding:1rem;background:linear-gradient(135deg,#0a66c2,#004182);color:#fff;border:none;border-radius:8px;font-size:1.1rem;cursor:pointer}
</style>
</head>
<body>
<div class="box">
<h2>🔐 Sign In</h2>
<form method="post">
<div class="group">
<label>Username (4+ chars)</label>
<input type="text" name="username" required minlength="4">
</div>
<div class="group">
<label>Password (4+ chars)</label>
<input type="password" name="password" required minlength="4">
</div>
<button type="submit" class="btn">Sign In</button>
</form>
</div>
</body>
</html>
    """)

def dashboard(request):
    tv = sum(VOTE_COUNT.values())
    ts = len(SURVEY_RESPONSES)
    return HttpResponse(f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Dashboard</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#0a66c2,#004182,#002855);height:100vh;overflow:hidden;font-size:16px}}
.toolbar{{background:#000;padding:0.5rem;display:flex;justify-content:center;gap:0.5rem;flex-wrap:wrap}}
.toolbar button{{padding:0.4rem 0.8rem;background:#333;color:#fff;border:1px solid #fff;border-radius:4px;cursor:pointer;font-size:0.85rem}}
.toolbar button:hover{{background:#fff;color:#000}}
.header{{background:#000;color:#fff;padding:0.5rem;text-align:center}}
.header h1{{font-size:1.2rem}}
.container{{max-width:1400px;margin:0.3rem auto;padding:0.3rem;height:calc(100vh - 120px);overflow:hidden}}
.welcome{{background:#fff;padding:0.8rem;border-radius:8px;text-align:center;margin-bottom:0.5rem}}
.welcome h2{{font-size:1.3rem;margin-bottom:0.3rem}}
.welcome p{{font-size:0.85rem;margin:0.3rem 0}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:0.5rem;margin-bottom:0.5rem}}
.stat{{background:#fff;padding:0.8rem;border-radius:8px;text-align:center}}
.stat-num{{font-size:2rem;font-weight:bold;color:#0a66c2}}
.stat div:last-child{{font-size:0.75rem}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:0.8rem}}
.card{{background:#fff;padding:1rem;border-radius:8px;text-align:center;transition:transform 0.3s}}
.card:hover{{transform:translateY(-3px)}}
.card h3{{margin:0.5rem 0;font-size:1rem}}
.card p{{font-size:0.8rem;margin:0.5rem 0}}
.btn{{padding:0.6rem 1rem;background:linear-gradient(135deg,#0a66c2,#004182);color:#fff;border:none;border-radius:6px;font-size:0.85rem;cursor:pointer;margin:0.3rem;text-decoration:none;display:inline-block}}
.btn:hover{{transform:translateY(-2px)}}
.btn-sec{{background:#fff;color:#0a66c2;border:2px solid #0a66c2}}
</style>
</head>
<body>
""" + TOOLBAR + f"""
<div class="header"><h1>Accessible Voting & Survey System</h1></div>
<div class="container">
<div class="welcome">
<h2>🎉 Welcome, {CURRENT_USER}!</h2>
<p style="font-weight:600;color:#0a66c2">💪 Ready to Make Your Voice Heard?</p>
<p style="font-size:0.75rem;color:#718096">✅ Data saved permanently!</p>
<button class="btn btn-sec" onclick="localStorage.removeItem('auth_token');window.location.href='/'">Logout</button>
</div>
<div class="stats">
<div class="stat"><div class="stat-num">{tv}</div><div>Total Votes</div></div>
<div class="stat"><div class="stat-num">{ts}</div><div>Surveys</div></div>
<div class="stat"><div class="stat-num">{len(CANDIDATES)}</div><div>Priorities</div></div>
<div class="stat"><div class="stat-num">🤖</div><div>AI Helper</div></div>
</div>
<div class="cards">
<div class="card"><div style="font-size:2.5rem">🗳️</div><h3>Vote Now</h3><p>Make your voice count!</p><a href="/vote/" class="btn">Vote</a></div>
<div class="card"><div style="font-size:2.5rem">📋</div><h3>Survey</h3><p>Share your story</p><a href="/survey/" class="btn">Survey</a></div>
<div class="card"><div style="font-size:2.5rem">📊</div><h3>Results</h3><p>See the impact</p><a href="/results/" class="btn">Results</a></div>
<div class="card"><div style="font-size:2.5rem">🤖</div><h3>AI Chat</h3><p>Get insights</p><a href="/chat/" class="btn">Chat</a></div>
</div>
</div>
</body>
</html>
    """)

def vote_page(request):
    cards = "".join([f"<div class='card' onclick='submitVote({c})'><h3>{CANDIDATES[c]}</h3><p>Click to vote</p></div>" for c in CANDIDATES])
    return HttpResponse(f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Vote</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#0a66c2,#004182,#002855);height:100vh;overflow:hidden;font-size:16px}}
.toolbar{{background:#000;padding:0.5rem;display:flex;justify-content:center;gap:0.5rem;flex-wrap:wrap}}
.toolbar button{{padding:0.4rem 0.8rem;background:#333;color:#fff;border:1px solid #fff;border-radius:4px;cursor:pointer;font-size:0.85rem}}
.toolbar button:hover{{background:#fff;color:#000}}
.header{{background:#000;color:#fff;padding:0.5rem;text-align:center}}
.header h1{{font-size:1.2rem}}
.container{{max-width:1200px;margin:0.3rem auto;padding:1rem;background:#fff;border-radius:12px;height:calc(100vh - 120px);overflow:hidden}}
.btn{{padding:0.6rem 1rem;background:linear-gradient(135deg,#0a66c2,#004182);color:#fff;border:none;border-radius:6px;font-size:0.85rem;cursor:pointer;margin-bottom:0.5rem;text-decoration:none;display:inline-block}}
.btn-sec{{background:#fff;color:#0a66c2;border:2px solid #0a66c2}}
.card{{background:#f7fafc;padding:1.2rem;border-radius:8px;margin:0.5rem;display:inline-block;min-width:200px;cursor:pointer;border:3px solid #e2e8f0;transition:all 0.3s}}
.card:hover{{border-color:#0a66c2;transform:translateY(-3px)}}
.card h3{{color:#0a66c2;margin-bottom:0.3rem;font-size:1rem}}
.card p{{font-size:0.8rem}}
h2{{color:#0a66c2;font-size:1.4rem;margin:0.5rem 0}}
</style>
<script>
async function submitVote(c){{
const t=localStorage.getItem('auth_token');
if(!t){{alert('Login first!');window.location.href='/signin/';return;}}
try{{
const r=await fetch('/api/vote/',{{method:'POST',headers:{{'Content-Type':'application/json','Authorization':'Bearer '+t}},body:JSON.stringify({{candidate_id:c}})}});
const d=await r.json();
if(d.success){{alert('✅ Vote saved!');window.location.href='/app/';}}
else alert('❌ '+d.message);
}}catch(e){{alert('Error: '+e.message);}}
}}
</script>
</head>
<body>
""" + TOOLBAR + f"""
<div class="header"><h1>Accessible Voting & Survey System</h1></div>
<div class="container">
<a href="/app/" class="btn btn-sec">⬅ Back</a>
<h2>🗳️ Cast Your Vote</h2>
<p style="margin:0.5rem 0;font-size:0.9rem">Choose your priority (or use 🎤 Voice):</p>
<div style="text-align:center">{cards}</div>
</div>
</body>
</html>
    """)

def survey_page(request):
    qs = ""
    for i in range(len(SURVEY_QUESTIONS)):
        qs += f"""
        <div class='q' id='q{i}'>
            <p><b>{i+1}. {SURVEY_QUESTIONS[i]}</b></p>
            <button type='button' class='btn-voice' onclick='readQuestion({i})' title='Read question aloud'>🔊 Read</button>
            <button type='button' class='btn-voice' onclick='answerByVoice({i})' title='Answer by voice' style='background:#28a745'>🎤 Voice Answer</button>
            <div class='r'>
                <label><input type='radio' name='q{i}' value='Yes' required> Yes</label>
                <label><input type='radio' name='q{i}' value='No' required> No</label>
                <label><input type='radio' name='q{i}' value='Partially' required> Partially</label>
            </div>
            <div id='answer{i}' class='selected-answer'></div>
        </div>
        """
    
    return HttpResponse(f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Survey</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#0a66c2,#004182,#002855);min-height:100vh;overflow-y:auto;font-size:16px}}
.toolbar{{background:#000;padding:0.5rem;display:flex;justify-content:center;gap:0.5rem;flex-wrap:wrap}}
.toolbar button{{padding:0.4rem 0.8rem;background:#333;color:#fff;border:1px solid #fff;border-radius:4px;cursor:pointer;font-size:0.85rem}}
.toolbar button:hover{{background:#fff;color:#000}}
.header{{background:#000;color:#fff;padding:0.5rem;text-align:center}}
.header h1{{font-size:1.2rem}}
.container{{max-width:1000px;margin:0.5rem auto;padding:1.5rem;background:#fff;border-radius:12px;margin-bottom:2rem}}
.btn{{padding:0.6rem 1rem;background:linear-gradient(135deg,#0a66c2,#004182);color:#fff;border:none;border-radius:6px;font-size:0.85rem;cursor:pointer;margin:0.3rem;text-decoration:none;display:inline-block}}
.btn-sec{{background:#fff;color:#0a66c2;border:2px solid #0a66c2}}
.btn-voice{{padding:0.4rem 0.8rem;background:#0a66c2;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:0.8rem;margin:0 0.3rem}}
.q{{background:#f7fafc;padding:1rem;border-radius:8px;margin:0.8rem 0;border-left:4px solid #0a66c2}}
.r{{display:flex;gap:1.5rem;margin-top:0.5rem;flex-wrap:wrap}}
.r label{{display:flex;align-items:center;gap:0.5rem;font-size:0.9rem;cursor:pointer}}
.selected-answer{{margin-top:0.5rem;padding:0.5rem;background:#d4edda;border-radius:4px;font-weight:600;color:#155724;display:none}}
h2{{color:#0a66c2;font-size:1.4rem;margin:0.5rem 0}}
</style>
<script>
const questions = {json.dumps(SURVEY_QUESTIONS)};

function readQuestion(i) {{
    const text = questions[i];
    speak(text);
}}

function answerByVoice(i) {{
    if(!('webkitSpeechRecognition' in window)) {{
        alert('Voice recognition not supported. Please use Chrome browser!');
        return;
    }}
    
    const recognition = new webkitSpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = false;
    
    speak('Please say Yes, No, or Partially');
    
    recognition.onresult = function(event) {{
        const transcript = event.results[0][0].transcript.toLowerCase();
        console.log('Voice input:', transcript);
        
        let answer = null;
        if(transcript.includes('yes')) answer = 'Yes';
        else if(transcript.includes('no')) answer = 'No';
        else if(transcript.includes('partial')) answer = 'Partially';
        
        if(answer) {{
            const radio = document.querySelector(`input[name='q${{i}}'][value='${{answer}}']`);
            if(radio) {{
                radio.checked = true;
                document.getElementById('answer' + i).textContent = '✅ Answered: ' + answer;
                document.getElementById('answer' + i).style.display = 'block';
                speak('You answered ' + answer);
            }}
        }} else {{
            speak('Sorry, I did not understand. Please say Yes, No, or Partially');
        }}
    }};
    
    recognition.onerror = function(event) {{
        console.error('Recognition error:', event.error);
        speak('Voice recognition error. Please try again.');
    }};
    
    recognition.start();
}}

function speak(text) {{
    if('speechSynthesis' in window) {{
        speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.9;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        speechSynthesis.speak(utterance);
    }}
}}

async function submitSurvey() {{
    const token = localStorage.getItem('auth_token');
    if(!token) {{
        alert('Please login first!');
        window.location.href = '/signin/';
        return;
    }}
    
    const form = document.getElementById('surveyForm');
    const formData = new FormData(form);
    const responses = [];
    
    for(let i = 0; i < 10; i++) {{
        const answer = formData.get('q' + i);
        if(!answer) {{
            alert('❌ Please answer question ' + (i + 1));
            speak('Please answer question ' + (i + 1));
            return;
        }}
        responses.push(answer);
    }}
    
    console.log('Submitting responses:', responses);
    
    try {{
        const response = await fetch('/api/survey/submit/', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            }},
            body: JSON.stringify({{responses: responses}})
        }});
        
        const data = await response.json();
        console.log('Server response:', data);
        
        if(data.success) {{
            alert('✅ Survey submitted and saved permanently!');
            speak('Survey submitted successfully');
            window.location.href = '/app/';
        }} else {{
            alert('❌ Error: ' + data.message);
            speak('Error: ' + data.message);
        }}
    }} catch(error) {{
        console.error('Submission error:', error);
        alert('❌ Error submitting survey: ' + error.message);
    }}
}}

window.addEventListener('DOMContentLoaded', function() {{
    speak('Survey page loaded. You can click the microphone button to answer by voice, or click the speaker button to hear each question.');
}});
</script>
</head>
<body>
""" + TOOLBAR + f"""
<div class="header"><h1>Accessible Voting & Survey System</h1></div>
<div class="container">
<a href="/app/" class="btn btn-sec">⬅ Back to Dashboard</a>
<h2>📋 Accessibility Survey</h2>
<p style="margin:0.5rem 0;font-size:0.9rem">Answer all questions (click 🔊 to hear question, 🎤 to answer by voice):</p>
<form id="surveyForm">
{qs}
<button type="button" class="btn" onclick="submitSurvey()" style="margin-top:1rem;padding:1rem 2rem;font-size:1rem">Submit Survey</button>
</form>
</div>
</body>
</html>
    """)

def results_page(request):
    tv = sum(VOTE_COUNT.values())
    ts = len(SURVEY_RESPONSES)
    
    rh = "<h3>🗳️ Voting Results</h3>"
    if tv > 0:
        for c, n in CANDIDATES.items():
            v = VOTE_COUNT[c]
            p = (v/tv)*100
            rh += f"<div style='margin:1rem 0'><div style='display:flex;justify-content:space-between;margin-bottom:0.5rem'><b>{n}</b><span>{v} votes ({p:.1f}%)</span></div><div style='background:#e2e8f0;height:30px;border-radius:8px;overflow:hidden'><div style='width:{p}%;background:linear-gradient(135deg,#0a66c2,#004182);height:100%'></div></div></div>"
    else:
        rh += "<p>No votes yet.</p>"
    
    rh += "<h3 style='margin-top:2rem'>📋 Survey Stats</h3>"
    if ts > 0:
        ay = sum(1 for r in SURVEY_RESPONSES for a in r if a=='Yes')
        an = sum(1 for r in SURVEY_RESPONSES for a in r if a=='No')
        ap = sum(1 for r in SURVEY_RESPONSES for a in r if a=='Partially')
        t = ay+an+ap
        if t > 0:
            rh += f"<p style='margin:1rem 0'>✅ Yes: {ay} ({(ay/t)*100:.1f}%) | ❌ No: {an} ({(an/t)*100:.1f}%) | ⚠️ Partially: {ap} ({(ap/t)*100:.1f}%)</p>"
    else:
        rh += "<p>No surveys yet.</p>"
    
    return HttpResponse(f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Results</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#0a66c2,#004182,#002855);height:100vh;overflow:hidden;font-size:16px}}
.toolbar{{background:#000;padding:0.5rem;display:flex;justify-content:center;gap:0.5rem;flex-wrap:wrap}}
.toolbar button{{padding:0.4rem 0.8rem;background:#333;color:#fff;border:1px solid #fff;border-radius:4px;cursor:pointer;font-size:0.85rem}}
.toolbar button:hover{{background:#fff;color:#000}}
.header{{background:#000;color:#fff;padding:0.5rem;text-align:center}}
.header h1{{font-size:1.2rem}}
.container{{max-width:1000px;margin:0.3rem auto;padding:1.5rem;background:#fff;border-radius:12px;height:calc(100vh - 120px);overflow:hidden}}
.btn{{padding:0.6rem 1rem;background:linear-gradient(135deg,#0a66c2,#004182);color:#fff;border:none;border-radius:6px;font-size:0.85rem;cursor:pointer;margin-bottom:0.5rem;text-decoration:none;display:inline-block}}
.btn-sec{{background:#fff;color:#0a66c2;border:2px solid #0a66c2}}
h2{{color:#0a66c2;font-size:1.4rem;margin:0.5rem 0}}
h3{{color:#0a66c2;margin:1rem 0 0.5rem 0;font-size:1.2rem}}
</style>
</head>
<body>
""" + TOOLBAR + f"""
<div class="header"><h1>Accessible Voting & Survey System</h1></div>
<div class="container">
<a href="/app/" class="btn btn-sec">⬅ Back</a>
<h2>📊 Live Results</h2>
<p style="margin:0.5rem 0;font-size:0.9rem">✅ Data saved permanently!</p>
{rh}
</div>
</body>
</html>
    """)

def chat_page(request):
    return HttpResponse("""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>AI Chat</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#0a66c2,#004182,#002855);height:100vh;overflow:hidden;font-size:16px}
.toolbar{background:#000;padding:0.5rem;display:flex;justify-content:center;gap:0.5rem;flex-wrap:wrap}
.toolbar button{padding:0.4rem 0.8rem;background:#333;color:#fff;border:1px solid #fff;border-radius:4px;cursor:pointer;font-size:0.85rem}
.toolbar button:hover{background:#fff;color:#000}
.header{background:#000;color:#fff;padding:0.5rem;text-align:center}
.header h1{font-size:1.2rem}
.container{max-width:1000px;margin:0.3rem auto;padding:1.5rem;background:#fff;border-radius:12px;height:calc(100vh - 120px);overflow:hidden}
.btn{padding:0.6rem 1rem;background:linear-gradient(135deg,#0a66c2,#004182);color:#fff;border:none;border-radius:6px;font-size:0.85rem;cursor:pointer;margin:0.3rem;text-decoration:none;display:inline-block}
.btn-sec{background:#fff;color:#0a66c2;border:2px solid #0a66c2}
.box{background:#f7fafc;padding:1rem;border-radius:8px;max-height:350px;overflow-y:auto;margin:0.8rem 0}
.msg{padding:0.8rem;margin:0.4rem 0;border-radius:8px;font-size:0.9rem}
.user{background:#0a66c2;color:#fff;text-align:right}
.ai{background:#fff;border:2px solid #e2e8f0}
.inp{display:flex;gap:0.8rem;margin:0.8rem 0}
.inp input{flex:1;padding:0.7rem;border:2px solid #e2e8f0;border-radius:8px;font-size:0.9rem}
h2{color:#0a66c2;font-size:1.4rem;margin:0.5rem 0}
</style>
<script>
async function send(){
const i=document.getElementById('i');
const q=i.value.trim();
if(!q)return;
const b=document.getElementById('b');
b.innerHTML+='<div class="msg user">👤 '+q+'</div>';
i.value='';
try{
const r=await fetch('/api/chat/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});
const d=await r.json();
b.innerHTML+='<div class="msg ai">🤖 '+(d.answer||'Error').replace(/\\n/g,'<br>')+'</div>';
b.scrollTop=b.scrollHeight;
}catch(e){b.innerHTML+='<div class="msg ai">⚠️ Error</div>';}
}
function q(t){document.getElementById('i').value=t;send();}
</script>
</head>
<body>
""" + TOOLBAR + """
<div class="header"><h1>Accessible Voting & Survey System</h1></div>
<div class="container">
<a href="/app/" class="btn btn-sec">⬅ Back</a>
<h2>🤖 AI Assistant</h2>
<p style="margin:0.5rem 0;font-size:0.9rem">Ask about data:</p>
<div id="b" class="box">
<div style="color:#718096;padding:1.5rem;text-align:center">💬 Ask me...</div>
</div>
<div class="inp">
<input type="text" id="i" placeholder="Type question..." onkeypress="if(event.key==='Enter')send()">
<button class="btn" onclick="send()">Send</button>
</div>
<div>
<button class="btn btn-sec" onclick="q('What are the voting results?')">📊 Results</button>
<button class="btn btn-sec" onclick="q('Show survey statistics')">📋 Survey</button>
<button class="btn btn-sec" onclick="q('help')">❓ Help</button>
</div>
</div>
</body>
</html>
    """)

def serve_image(request):
    """Serve collage image"""
    path = os.path.join(os.path.dirname(__file__), 'accessibility-collage.jpg')
    try:
        with open(path, 'rb') as f:
            return HttpResponse(f.read(), content_type='image/jpeg')
    except:
        return HttpResponse("Image not found", status=404)

# ============================================
# API ENDPOINTS
# ============================================

@csrf_exempt
def api_vote(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST'}, status=405)
    
    auth = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
    if auth not in VALID_TOKENS:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=401)
    
    try:
        data = json.loads(request.body)
        cid = int(data.get('candidate_id'))
        
        if cid not in CANDIDATES:
            return JsonResponse({'success': False, 'message': 'Invalid candidate'}, status=400)
        
        user = VALID_TOKENS[auth]
        if user in VOTERS[cid]:
            return JsonResponse({'success': False, 'message': 'Already voted'}, status=400)
        
        VOTE_COUNT[cid] += 1
        VOTERS[cid].append(user)
        save_data()
        
        return JsonResponse({'success': True, 'message': f'Voted for {CANDIDATES[cid]}'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
def api_survey(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST'}, status=405)
    
    auth = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
    if auth not in VALID_TOKENS:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=401)
    
    try:
        data = json.loads(request.body)
        resp = data.get('responses', [])
        
        if len(resp) != len(SURVEY_QUESTIONS):
            return JsonResponse({'success': False, 'message': 'Need all answers'}, status=400)
        
        SURVEY_RESPONSES.append(resp)
        save_data()
        
        return JsonResponse({'success': True, 'message': 'Survey saved'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
def api_chat(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST'}, status=405)
    
    try:
        data = json.loads(request.body)
        q = data.get('question', '').strip()
        if not q:
            return JsonResponse({'success': False, 'message': 'Question required'}, status=400)
        
        answer = get_response(q)
        return JsonResponse({'success': True, 'answer': answer})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

# ============================================
# URL CONFIGURATION
# ============================================

urlpatterns = [
    path('', welcome),
    path('signin/', login),
    path('app/', dashboard),
    path('vote/', vote_page),
    path('survey/', survey_page),
    path('results/', results_page),
    path('chat/', chat_page),
    path('images/collage.jpg', serve_image),
    path('api/vote/', api_vote),
    path('api/survey/submit/', api_survey),
    path('api/chat/', api_chat),
]

application = get_wsgi_application()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        sys.argv.append('runserver')
    execute_from_command_line(sys.argv)
