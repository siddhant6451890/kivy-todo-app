import json, os, threading, urllib.request, urllib.error
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.graphics import Color, RoundedRectangle

API_KEY = "AIzaSyAs-3lnqFzuYOgowJ3F_TWbnVsn4PNSCvs"
SIGNUP = "https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=" + API_KEY
LOGIN = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=" + API_KEY

class RoundedBox(BoxLayout):
    def __init__(self, bg_color=(.15,.15,.22,1), **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self.bg=Color(*bg_color)
            self.rect=RoundedRectangle(pos=self.pos,size=self.size,radius=[15])
        self.bind(pos=self.update_rect,size=self.update_rect)
    def update_rect(self,*args):
        self.rect.pos=self.pos; self.rect.size=self.size

class TodoApp(App):
    def build(self):
        self.current_user=None; self.tasks=[]; self.current_filter="ALL"
        self.stopwatch_seconds=0; self.stopwatch_event=None
        self.root_layout=BoxLayout(orientation="vertical",padding=15,spacing=10)
        self.show_login()
        return self.root_layout

    def clear(self): self.root_layout.clear_widgets()

    def msg(self,title,text):
        box=BoxLayout(orientation="vertical",padding=15,spacing=10)
        box.add_widget(Label(text=text))
        b=Button(text="OK",size_hint_y=None,height=55); box.add_widget(b)
        p=Popup(title=title,content=box,size_hint=(.85,.4))
        b.bind(on_press=lambda x:p.dismiss()); p.open()

    # ---------------- LOGIN / SIGNUP ----------------
    def show_login(self):
        self.clear()
        self.root_layout.add_widget(Label(text="[b][color=00aaff]MY TO-DO APP[/color][/b]",markup=True,font_size=28,size_hint_y=None,height=100))
        self.root_layout.add_widget(Label(text="Login to your account",font_size=18,size_hint_y=None,height=45))
        self.login_email=TextInput(hint_text="Email address",multiline=False,size_hint_y=None,height=55)
        self.login_password=TextInput(hint_text="Password",password=True,multiline=False,size_hint_y=None,height=55)
        login=Button(text="LOGIN",size_hint_y=None,height=60)
        signup=Button(text="CREATE NEW ACCOUNT",size_hint_y=None,height=60)
        for w in [self.login_email,self.login_password,login,signup]: self.root_layout.add_widget(w)
        login.bind(on_press=self.login); signup.bind(on_press=lambda x:self.show_signup())

    def show_signup(self):
        self.clear()
        self.root_layout.add_widget(Label(text="[b][color=00aaff]CREATE ACCOUNT[/color][/b]",markup=True,font_size=26,size_hint_y=None,height=100))
        self.signup_email=TextInput(hint_text="Email address",multiline=False,size_hint_y=None,height=55)
        self.signup_password=TextInput(hint_text="Password (minimum 6 characters)",password=True,multiline=False,size_hint_y=None,height=55)
        self.confirm_password=TextInput(hint_text="Confirm password",password=True,multiline=False,size_hint_y=None,height=55)
        create=Button(text="SIGN UP",size_hint_y=None,height=60); back=Button(text="BACK TO LOGIN",size_hint_y=None,height=55)
        for w in [self.signup_email,self.signup_password,self.confirm_password,create,back]: self.root_layout.add_widget(w)
        create.bind(on_press=self.signup); back.bind(on_press=lambda x:self.show_login())

    def firebase(self,url,payload,ok,fail):
        def work():
            try:
                req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"},method="POST")
                with urllib.request.urlopen(req,timeout=20) as r: result=json.loads(r.read().decode())
                Clock.schedule_once(lambda dt:ok(result))
            except urllib.error.HTTPError as e:
                try: error=json.loads(e.read().decode()).get("error",{}).get("message","Request failed")
                except: error=str(e)
                Clock.schedule_once(lambda dt:fail(error))
            except Exception as e: Clock.schedule_once(lambda dt:fail(str(e)))
        threading.Thread(target=work,daemon=True).start()

    def signup(self,*args):
        email=self.signup_email.text.strip(); pw=self.signup_password.text; confirm=self.confirm_password.text
        if not email or not pw or not confirm: return self.msg("Error","Please fill all fields.")
        if pw!=confirm: return self.msg("Error","Passwords do not match.")
        if len(pw)<6: return self.msg("Error","Password must be at least 6 characters.")
        self.firebase(SIGNUP,{"email":email,"password":pw,"returnSecureToken":True},self.auth_ok,self.auth_error)

    def login(self,*args):
        email=self.login_email.text.strip(); pw=self.login_password.text
        if not email or not pw: return self.msg("Error","Please enter email and password.")
        self.firebase(LOGIN,{"email":email,"password":pw,"returnSecureToken":True},self.auth_ok,self.auth_error)

    def auth_ok(self,data):
        self.current_user={"email":data.get("email",""),"uid":data.get("localId","")}
        self.open_app()

    def auth_error(self,error):
        nice={"EMAIL_EXISTS":"This email already has an account.","EMAIL_NOT_FOUND":"No account found with this email.","INVALID_PASSWORD":"Incorrect password.","INVALID_LOGIN_CREDENTIALS":"Invalid email or password.","INVALID_EMAIL":"Please enter a valid email."}
        self.msg("Login / Signup Error",nice.get(error,error.replace("_"," ")))

    def logout(self,*args):
        self.current_user=None; self.tasks=[]; self.show_login()

    # ---------------- MAIN APP ----------------
    def open_app(self):
        self.clear(); self.tasks=self.load_tasks(); self.current_filter="ALL"
        head=BoxLayout(size_hint_y=None,height=65,spacing=8)
        head.add_widget(Label(text="[b][color=00aaff]MY TO-DO APP[/color][/b]",markup=True,font_size=23))
        menu=Button(text="☰",font_size=28,size_hint_x=None,width=70); menu.bind(on_press=self.open_menu); head.add_widget(menu)
        self.root_layout.add_widget(head)
        self.root_layout.add_widget(Label(text="Welcome, "+self.current_user["email"],size_hint_y=None,height=30))
        self.counter=Label(text="",markup=True,size_hint_y=None,height=35); self.root_layout.add_widget(self.counter)
        self.search_input=TextInput(hint_text="Search tasks...",multiline=False,size_hint_y=None,height=50)
        self.search_input.bind(text=lambda a,b:self.show_tasks()); self.root_layout.add_widget(self.search_input)
        self.task_input=TextInput(hint_text="Enter new task...",multiline=False,size_hint_y=None,height=55)
        self.task_input.bind(on_text_validate=self.add_task); self.root_layout.add_widget(self.task_input)
        add=Button(text="ADD TASK",size_hint_y=None,height=55); add.bind(on_press=self.add_task); self.root_layout.add_widget(add)
        filters=BoxLayout(size_hint_y=None,height=50,spacing=5)
        for name in ["ALL","ACTIVE","DONE"]:
            b=Button(text=name); b.bind(on_press=lambda x,n=name:self.set_filter(n)); filters.add_widget(b)
        self.root_layout.add_widget(filters)
        self.task_list=BoxLayout(orientation="vertical",size_hint_y=None,spacing=8); self.task_list.bind(minimum_height=self.task_list.setter("height"))
        scroll=ScrollView(); scroll.add_widget(self.task_list); self.root_layout.add_widget(scroll)
        self.show_tasks()

    def open_menu(self,*args):
        box=BoxLayout(orientation="vertical",padding=10,spacing=8)
        items=[("⏱ STOPWATCH",self.open_stopwatch),("🗑 CLEAR COMPLETED",self.clear_completed),("ℹ ABOUT",self.show_about),("🚪 LOGOUT",self.logout)]
        p=Popup(title="☰ MENU",content=box,size_hint=(.9,.7))
        for text,fn in items:
            b=Button(text=text,size_hint_y=None,height=55); b.bind(on_press=lambda x,f=fn:(p.dismiss(),f())); box.add_widget(b)
        close=Button(text="CLOSE",size_hint_y=None,height=55); close.bind(on_press=lambda x:p.dismiss()); box.add_widget(close); p.open()

    def show_about(self,*args):
        self.msg("ABOUT","MY TO-DO APP\n\nVersion 3.0\n\nCreated by Siddhant Ojha\n\nFeatures:\nFirebase Login & Signup\nTasks • Photos • Search • Filters\nStopwatch • Menu • Logout")

    # ---------------- TASKS ----------------
    def set_filter(self,name): self.current_filter=name; self.show_tasks()
    def add_task(self,*args):
        text=self.task_input.text.strip()
        if text:
            self.tasks.append({"text":text,"completed":False,"photo":""}); self.task_input.text=""; self.save_tasks(); self.show_tasks()
    def toggle_done(self,task):
        task["completed"]=not task.get("completed",False); self.save_tasks(); self.show_tasks()
    def delete_task(self,task):
        if task in self.tasks: self.tasks.remove(task); self.save_tasks(); self.show_tasks()
    def clear_completed(self,*args):
        self.tasks=[t for t in self.tasks if not t.get("completed",False)]; self.save_tasks(); self.show_tasks()

    def edit_task(self,task):
        inp=TextInput(text=task.get("text",""),multiline=False)
        save=Button(text="SAVE"); cancel=Button(text="CANCEL")
        box=BoxLayout(orientation="vertical",padding=10,spacing=10); row=BoxLayout(size_hint_y=None,height=55); row.add_widget(save); row.add_widget(cancel); box.add_widget(inp); box.add_widget(row)
        p=Popup(title="EDIT TASK",content=box,size_hint=(.9,.4))
        def do_save(*x):
            if inp.text.strip(): task["text"]=inp.text.strip(); self.save_tasks(); self.show_tasks()
            p.dismiss()
        save.bind(on_press=do_save); cancel.bind(on_press=lambda x:p.dismiss()); p.open()

    def photo_clicked(self,task):
        chooser=FileChooserListView(filters=["*.jpg","*.jpeg","*.png"])
        select=Button(text="SELECT PHOTO",size_hint_y=None,height=60)
        box=BoxLayout(orientation="vertical"); box.add_widget(chooser); box.add_widget(select)
        p=Popup(title="Choose a Photo",content=box,size_hint=(.95,.95))
        def choose(*x):
            if chooser.selection: task["photo"]=chooser.selection[0]; self.save_tasks(); self.show_tasks()
            p.dismiss()
        select.bind(on_press=choose); p.open()

    def show_tasks(self):
        if not hasattr(self,"task_list"): return
        self.task_list.clear_widgets(); total=len(self.tasks); done=sum(t.get("completed",False) for t in self.tasks)
        self.counter.text=f"[color=00aaff]Total: {total}[/color]    [color=00ff88]Done: {done}[/color]"
        search=self.search_input.text.lower()
        for task in self.tasks:
            if search not in task.get("text","").lower(): continue
            if self.current_filter=="ACTIVE" and task.get("completed"): continue
            if self.current_filter=="DONE" and not task.get("completed"): continue
            card=RoundedBox(orientation="vertical",size_hint_y=None,height=150,spacing=5,padding=8)
            top=BoxLayout(spacing=8); photo=task.get("photo","")
            if photo and os.path.exists(photo): top.add_widget(Image(source=photo,size_hint_x=.25))
            prefix="DONE - " if task.get("completed") else "• "
            top.add_widget(Label(text=prefix+task.get("text",""),font_size=16))
            row=BoxLayout(size_hint_y=None,height=55,spacing=5)
            for text,fn in [("EDIT",self.edit_task),("PHOTO",self.photo_clicked),("UNDO" if task.get("completed") else "DONE",self.toggle_done),("DELETE",self.delete_task)]:
                b=Button(text=text); b.bind(on_press=lambda x,f=fn,t=task:f(t)); row.add_widget(b)
            card.add_widget(top); card.add_widget(row); self.task_list.add_widget(card)

    # ---------------- STOPWATCH ----------------
    def format_time(self):
        h=self.stopwatch_seconds//3600; m=(self.stopwatch_seconds%3600)//60; s=self.stopwatch_seconds%60
        return f"{h:02d}:{m:02d}:{s:02d}"
    def open_stopwatch(self,*args):
        self.sw_label=Label(text=self.format_time(),font_size=40)
        box=BoxLayout(orientation="vertical",padding=15,spacing=15); row=BoxLayout(size_hint_y=None,height=60)
        for text,fn in [("START",self.start_sw),("STOP",self.stop_sw),("RESET",self.reset_sw)]:
            b=Button(text=text); b.bind(on_press=fn); row.add_widget(b)
        box.add_widget(self.sw_label); box.add_widget(row); Popup(title="⏱ STOPWATCH",content=box,size_hint=(.9,.5)).open()
    def start_sw(self,*args):
        if not self.stopwatch_event: self.stopwatch_event=Clock.schedule_interval(self.tick,1)
    def tick(self,dt):
        self.stopwatch_seconds+=1
        if hasattr(self,"sw_label"): self.sw_label.text=self.format_time()
    def stop_sw(self,*args):
        if self.stopwatch_event: self.stopwatch_event.cancel(); self.stopwatch_event=None
    def reset_sw(self,*args):
        self.stop_sw(); self.stopwatch_seconds=0
        if hasattr(self,"sw_label"): self.sw_label.text=self.format_time()

    # ---------------- PER USER STORAGE ----------------
    def filename(self):
        return "tasks_"+self.current_user.get("uid","guest")+".json" if self.current_user else "tasks_guest.json"
    def save_tasks(self):
        try:
            with open(self.filename(),"w",encoding="utf-8") as f: json.dump(self.tasks,f,ensure_ascii=False)
        except Exception: pass
    def load_tasks(self):
        try:
            if os.path.exists(self.filename()):
                with open(self.filename(),"r",encoding="utf-8") as f: data=json.load(f)
                return [x if isinstance(x,dict) else {"text":x,"completed":False,"photo":""} for x in data]
        except Exception: pass
        return []

if __name__ == "__main__":
    TodoApp().run()
