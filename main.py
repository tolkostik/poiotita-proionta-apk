"""
Ποιότητα τροφίμων – σκανάρεις το barcode και παίρνεις βαθμό από 1 έως 10.
"""
import threading
import webbrowser

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import NoTransition
from kivy.utils import platform

import food as F
import health as H

IS_ANDROID = platform == "android"
Window.clearcolor = (0.955, 0.96, 0.955, 1)
GREY = "#6B7486"
ALERT_BG = {"red": [0.75, 0.15, 0.12, 1], "orange": [0.9, 0.5, 0.05, 1]}
LIGHT = {"χαμηλή": "#0F7B4F", "μέτρια": "#C98A00", "υψηλή": "#B4461B"}


def score_color(s):
    if s is None:
        return [0.55, 0.58, 0.63, 1]
    if s >= 8.5:
        return [0.06, 0.48, 0.31, 1]
    if s >= 7:
        return [0.36, 0.62, 0.2, 1]
    if s >= 5.5:
        return [0.85, 0.62, 0.05, 1]
    if s >= 4:
        return [0.88, 0.45, 0.12, 1]
    return [0.75, 0.2, 0.15, 1]


def gr(x):
    t = f"{x:.1f}".replace(".", ",")
    return t[:-2] if t.endswith(",0") else t


def euro(x):
    return f"{x:.2f}".replace(".", ",") + " €"


def esc(t):
    return str(t).replace("&", "&amp;").replace("[", "&bl;").replace("]", "&br;")


KV = """
#:import dp kivy.metrics.dp

<Txt@Label>:
    size_hint_y: None
    markup: True
    color: 0.11, 0.14, 0.2, 1
    halign: 'left'
    valign: 'top'
    text_size: self.width - dp(28), None
    height: self.texture_size[1] + dp(12)
    padding: dp(14), dp(6)

<Row>:
    size_hint_y: None
    markup: True
    color: 0.11, 0.14, 0.2, 1
    halign: 'left'
    valign: 'middle'
    text_size: self.width - dp(100), None
    height: max(self.texture_size[1] + dp(22), dp(64))
    padding: dp(18), dp(10)
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        RoundedRectangle:
            pos: self.x + dp(8), self.y + dp(3)
            size: self.width - dp(16), self.height - dp(6)
            radius: [dp(10)]
        Color:
            rgba: self.badge
        Ellipse:
            pos: self.right - dp(66), self.center_y - dp(22)
            size: dp(44), dp(44)
    Label:
        text: root.score_text
        bold: True
        color: 1, 1, 1, 1
        font_size: '15sp'
        center_x: root.right - dp(44)
        center_y: root.center_y

<Banner>:
    size_hint_y: None
    markup: True
    color: 1, 1, 1, 1
    halign: 'left'
    valign: 'middle'
    text_size: self.width - dp(36), None
    height: self.texture_size[1] + dp(24)
    padding: dp(18), dp(12)
    canvas.before:
        Color:
            rgba: self.bg
        RoundedRectangle:
            pos: self.x + dp(6), self.y + dp(2)
            size: self.width - dp(12), self.height - dp(4)
            radius: [dp(10)]

<Cell@Label>:
    bg: [1, 1, 1, 1]
    markup: True
    color: 0.11, 0.14, 0.2, 1
    font_size: '14sp'
    halign: 'center'
    valign: 'middle'
    text_size: self.width - dp(8), None
    canvas.before:
        Color:
            rgba: self.bg
        Rectangle:
            pos: self.pos
            size: self.size

<Badge>:
    size_hint: None, None
    size: dp(120), dp(120)
    bold: True
    font_size: '34sp'
    color: 1, 1, 1, 1
    canvas.before:
        Color:
            rgba: self.bg
        Ellipse:
            pos: self.pos
            size: self.size

<RotCamera@Camera>:
    canvas.before:
        PushMatrix
        Rotate:
            angle: -90 if app.is_android else 0
            origin: self.center
    canvas.after:
        PopMatrix

<Nav@ToggleButton>:
    group: 'nav'
    allow_no_selection: False
    font_size: '12sp'
    background_normal: ''
    background_down: ''
    background_color: (0.95, 0.71, 0.14, 1) if self.state == 'down' else (0.11, 0.14, 0.2, 1)
    color: (0.11, 0.14, 0.2, 1) if self.state == 'down' else (1, 1, 1, 1)

<Root>:
    orientation: 'vertical'
    BoxLayout:
        size_hint_y: None
        height: dp(56)
        padding: dp(14), dp(8)
        canvas.before:
            Color:
                rgba: 0.11, 0.14, 0.2, 1
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: 'Ποιότητα τροφίμων'
            bold: True
            font_size: '19sp'
            halign: 'left'
            valign: 'middle'
            text_size: self.size
        Button:
            text: 'Προφίλ υγείας'
            bold: True
            size_hint_x: None
            width: dp(130)
            background_normal: ''
            background_color: 0.95, 0.71, 0.14, 1
            color: 0.11, 0.14, 0.2, 1
            on_release: app.show_profile()
    ScreenManager:
        id: sm
        Screen:
            name: 'scan'
            BoxLayout:
                orientation: 'vertical'
                FloatLayout:
                    id: cam_holder
                    canvas.before:
                        Color:
                            rgba: 0.08, 0.09, 0.11, 1
                        Rectangle:
                            pos: self.pos
                            size: self.size
                    Label:
                        id: cam_msg
                        text: 'Ενεργοποίηση κάμερας…'
                        color: 1, 1, 1, 0.8
                        pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                        text_size: self.parent.width - dp(40) if self.parent else 300, None
                        halign: 'center'
                Label:
                    id: scan_status
                    size_hint_y: None
                    height: dp(44)
                    color: 0.11, 0.14, 0.2, 1
                    text: 'Στόχευσε το barcode της συσκευασίας'
                    text_size: self.width - dp(20), None
                    halign: 'center'
                BoxLayout:
                    size_hint_y: None
                    height: dp(56)
                    padding: dp(10), dp(6)
                    spacing: dp(8)
                    TextInput:
                        id: code_in
                        hint_text: 'ή γράψε τον κωδικό barcode'
                        input_filter: 'int'
                        multiline: False
                        font_size: '17sp'
                        on_text_validate: app.lookup(self.text)
                    Button:
                        text: 'ΕΛΕΓΧΟΣ'
                        bold: True
                        size_hint_x: None
                        width: dp(110)
                        background_normal: ''
                        background_color: 0.95, 0.71, 0.14, 1
                        color: 0.11, 0.14, 0.2, 1
                        on_release: app.lookup(code_in.text)
        Screen:
            name: 'search'
            BoxLayout:
                orientation: 'vertical'
                BoxLayout:
                    size_hint_y: None
                    height: dp(56)
                    padding: dp(10), dp(6)
                    spacing: dp(8)
                    TextInput:
                        id: search_in
                        hint_text: 'π.χ. γάλα, γιαούρτι, δημητριακά'
                        multiline: False
                        font_size: '17sp'
                        on_text_validate: app.do_search(self.text)
                    Button:
                        text: 'ΑΝΑΖΗΤΗΣΗ'
                        bold: True
                        size_hint_x: None
                        width: dp(120)
                        background_normal: ''
                        background_color: 0.95, 0.71, 0.14, 1
                        color: 0.11, 0.14, 0.2, 1
                        on_release: app.do_search(search_in.text)
                ScrollView:
                    do_scroll_x: False
                    BoxLayout:
                        id: search_list
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: dp(2)
                        padding: 0, dp(6)
        Screen:
            name: 'history'
            ScrollView:
                do_scroll_x: False
                BoxLayout:
                    id: hist_list
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(2)
                    padding: 0, dp(6)
        Screen:
            name: 'add'
            ScrollView:
                do_scroll_x: False
                BoxLayout:
                    id: add_box
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(6)
                    padding: dp(12), dp(10)
        Screen:
            name: 'prices'
            BoxLayout:
                orientation: 'vertical'
                BoxLayout:
                    size_hint_y: None
                    height: dp(52)
                    padding: dp(10), dp(6)
                    spacing: dp(8)
                    Label:
                        text: 'Περιοχή:'
                        color: 0.11, 0.14, 0.2, 1
                        size_hint_x: None
                        width: dp(80)
                    Spinner:
                        id: region_filter
                        text: 'Όλες'
                        on_text: app.show_prices()
                ScrollView:
                    do_scroll_x: False
                    BoxLayout:
                        id: price_list
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: dp(2)
                        padding: 0, dp(6)
        Screen:
            name: 'profile'
            ScrollView:
                do_scroll_x: False
                BoxLayout:
                    id: profile_box
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(4)
                    padding: dp(12), dp(10)
        Screen:
            name: 'compare'
            ScrollView:
                do_scroll_x: False
                BoxLayout:
                    id: compare_box
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(4)
                    padding: dp(8), dp(10)
        Screen:
            name: 'result'
            ScrollView:
                do_scroll_x: False
                BoxLayout:
                    id: result_box
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(6)
                    padding: dp(6), dp(10)
    BoxLayout:
        size_hint_y: None
        height: dp(56)
        Nav:
            id: nav_scan
            text: 'Σκανάρισμα'
            state: 'down'
            on_release: app.go('scan')
        Nav:
            id: nav_search
            text: 'Αναζήτηση'
            on_release: app.go('search')
        Nav:
            id: nav_hist
            text: 'Ιστορικό'
            on_release: app.go('history')
        Nav:
            id: nav_prices
            text: 'Τιμές'
            on_release: app.go('prices')
        Nav:
            id: nav_compare
            text: 'Σύγκριση'
            on_release: app.go('compare')
"""


class Row(ButtonBehavior, Label):
    badge = ListProperty([0.5, 0.5, 0.5, 1])
    score_text = StringProperty("")
    code = StringProperty("")


class Banner(Label):
    bg = ListProperty([0.75, 0.15, 0.12, 1])


class Badge(Label):
    bg = ListProperty([0.5, 0.5, 0.5, 1])


class Root(BoxLayout):
    pass


Builder.load_string(KV)


class PoiotitaApp(App):
    title = "Poiotita"
    is_android = BooleanProperty(IS_ANDROID)

    def build(self):
        F.set_dir(self.user_data_dir)
        self.root_w = Root()
        self.root_w.ids.sm.transition = NoTransition()
        self.camera = None
        self.scanning = False
        self.decoding = False
        self.busy = False
        self.decoder = None
        try:
            from pyzbar.pyzbar import ZBarSymbol, decode
            syms = [ZBarSymbol.EAN13, ZBarSymbol.EAN8, ZBarSymbol.UPCA, ZBarSymbol.UPCE, ZBarSymbol.CODE128]
            self.decoder = lambda data, w, h: decode((data, w, h), symbols=syms)
        except Exception:  # noqa: BLE001
            self.decoder = None
        self.root_w.ids.cam_holder.bind(size=self._place_camera, pos=self._place_camera)
        Clock.schedule_once(lambda dt: self._ask_camera(), 0.5)
        Clock.schedule_interval(self._scan_tick, 0.4)
        self.show_history()
        return self.root_w

    # ------------------------------------------------------------ πλοήγηση
    def go(self, name):
        sm = self.root_w.ids.sm
        sm.current = name
        if name == "history":
            self.show_history()
        if name == "prices":
            self.show_prices()
        if name == "compare":
            self.show_compare()
        self._set_camera(name == "scan")
        navs = {"scan": "nav_scan", "search": "nav_search", "history": "nav_hist", "prices": "nav_prices",
                "compare": "nav_compare"}
        for scr, nid in navs.items():
            self.root_w.ids[nid].state = "down" if scr == name else "normal"

    # ------------------------------------------------------------ κάμερα
    def _ask_camera(self):
        if self.decoder is None:
            self.root_w.ids.cam_msg.text = ("Η ανάγνωση barcode με την κάμερα δεν είναι διαθέσιμη σε αυτή τη "
                                            "συσκευή. Γράψε τον κωδικό από κάτω.")
            return
        if not IS_ANDROID:
            self._start_camera()
            return
        try:
            from android.permissions import Permission, check_permission, request_permissions
            if check_permission(Permission.CAMERA):
                self._start_camera()
            else:
                def cb(perms, grants):
                    Clock.schedule_once(lambda dt: self._start_camera() if all(grants) else self._no_camera())
                request_permissions([Permission.CAMERA], cb)
        except Exception:  # noqa: BLE001
            self._start_camera()

    def _no_camera(self):
        self.root_w.ids.cam_msg.text = ("Δεν δόθηκε άδεια για την κάμερα. Μπορείς να γράψεις τον κωδικό από κάτω "
                                        "ή να δώσεις άδεια από τις Ρυθμίσεις του κινητού.")

    def _start_camera(self):
        try:
            from kivy.factory import Factory
            self.camera = Factory.RotCamera(index=0, resolution=(640, 480), play=True, allow_stretch=True,
                                            size_hint=(None, None))
            self.root_w.ids.cam_holder.add_widget(self.camera)
            self.root_w.ids.cam_msg.text = ""
            self._place_camera()
            self.scanning = True
        except Exception as e:  # noqa: BLE001
            self.camera = None
            self.root_w.ids.cam_msg.text = f"Η κάμερα δεν άνοιξε ({str(e)[:60]}). Γράψε τον κωδικό από κάτω."

    def _place_camera(self, *a):
        if not self.camera:
            return
        h = self.root_w.ids.cam_holder
        self.camera.size = (h.height, h.width) if IS_ANDROID else h.size
        self.camera.center = h.center

    def _set_camera(self, on):
        if self.camera:
            self.camera.play = on
        self.scanning = bool(on and self.camera)

    def _scan_tick(self, dt):
        if not (self.scanning and self.camera and self.decoder) or self.decoding or self.busy:
            return
        tex = self.camera.texture
        if tex is None:
            return
        try:
            pixels = tex.pixels
        except Exception:  # noqa: BLE001
            return
        w, h = tex.size
        self.decoding = True

        def work():
            code = None
            try:
                gray = pixels[1::4]  # πράσινο κανάλι ≈ ασπρόμαυρη εικόνα
                res = self.decoder(gray, w, h)
                if res:
                    code = res[0].data.decode("ascii", "ignore")
            except Exception:  # noqa: BLE001
                code = None
            Clock.schedule_once(lambda dt: self._decoded(code))

        threading.Thread(target=work, daemon=True).start()

    def _decoded(self, code):
        self.decoding = False
        if code and self.scanning:
            self.root_w.ids.scan_status.text = f"Βρέθηκε: {code}"
            self.lookup(code)

    # ------------------------------------------------------------ αναζήτηση προϊόντος
    def lookup(self, code):
        code = F.clean_code(code)
        if self.busy or len(code) < 6:
            if len(code) < 6:
                self.root_w.ids.scan_status.text = "Γράψε ολόκληρο τον κωδικό (8 ή 13 ψηφία)."
            return
        self.busy = True
        self.scanning = False
        self.root_w.ids.scan_status.text = f"Αναζήτηση προϊόντος {code}…"

        def work():
            try:
                p = F.fetch_product(code)
                err = None if p else "NOTFOUND"
            except Exception as e:  # noqa: BLE001
                p, err = None, f"Δεν ήταν δυνατή η αναζήτηση ({str(e)[:80]}). Έλεγξε τη σύνδεση."
            Clock.schedule_once(lambda dt: self._got(p, err, code))

        threading.Thread(target=work, daemon=True).start()

    def _got(self, p, err, code=""):
        self.busy = False
        if err == "NOTFOUND":
            self.show_add_form(code)
            return
        if err:
            if self.root_w.ids.sm.current != "scan":
                self.go("scan")
            self.root_w.ids.scan_status.text = err
            Clock.schedule_once(lambda dt: setattr(self, "scanning", bool(self.camera)), 2.5)
            return
        self.show_result(p)

    def show_result(self, p, record=True):
        d = F.score_details(p)
        s, why = d["score"], d["why"]
        if record:
            F.add_history(p, s)
        box = self.root_w.ids.result_box
        box.clear_widgets()
        from kivy.factory import Factory
        T = Factory.Txt

        top = BoxLayout(size_hint_y=None, height=dp(140), padding=(dp(14), dp(10)), spacing=dp(14))
        top.add_widget(Badge(text=gr(s) if s is not None else "–", bg=score_color(s)))
        conf = f"\n[size=12sp][color={GREY}]Αξιοπιστία βαθμού: {d['confidence']}[/color][/size]" if d["confidence"] else ""
        top.add_widget(T(text=f"[size=13sp][color={GREY}]Βαθμός ποιότητας στα 10[/color][/size]\n"
                              f"[size=22sp][b]{F.verdict(s)}[/b][/size]\n{esc(F.name_of(p))}{conf}", size_hint_y=None))
        box.add_widget(top)

        alerts = H.check(p)
        lvl = H.worst(alerts)
        if lvl:
            head = "ΑΚΑΤΑΛΛΗΛΟ ΓΙΑ ΤΟ ΠΡΟΦΙΛ ΣΟΥ" if lvl == "red" else "ΠΡΟΣΟΧΗ"
            box.add_widget(Banner(text=f"[size=18sp][b]{head}[/b][/size]\n" +
                                       "\n".join("• " + esc(m) for _, m in alerts), bg=ALERT_BG[lvl]))
            if lvl == "red" and record:
                self._vibrate()

        # φωτογραφία (κατεβαίνει στο παρασκήνιο)
        url = F.image_url(p)
        if url:
            img = Factory.Image(size_hint_y=None, height=dp(180), fit_mode="contain")
            box.add_widget(img)

            def load():
                try:
                    path = F.download_image(url, p.get("code"))
                except Exception:  # noqa: BLE001
                    path = None
                Clock.schedule_once(lambda dt: setattr(img, "source", path) if path else setattr(img, "height", 0))
            threading.Thread(target=load, daemon=True).start()

        warn = [x for x in F.allergens(p)[0]]
        labels = F.labels(p)
        palm = F.palm_oil(p)
        chips = []
        if labels:
            chips.append("[color=#0F7B4F][b]" + " · ".join(esc(x) for x in labels) + "[/b][/color]")
        if palm:
            chips.append(f"[color={'#B4461B' if 'Περιέχει' in palm else '#0F7B4F'}]{palm}[/color]")
        eco = F.eco_grade(p)
        if eco:
            chips.append(f"Περιβαλλοντικό σκορ: [b]{eco}[/b]")
        if chips:
            box.add_widget(T(text="\n".join(chips)))

        box.add_widget(T(text="[b]Πώς βγήκε ο βαθμός[/b]\n" + "\n".join("• " + esc(w) for w in why)))
        if s is None:
            add = Factory.Button(text="ΠΡΟΣΘΗΚΗ ΣΤΟΙΧΕΙΩΝ ΕΤΙΚΕΤΑΣ", bold=True, size_hint_y=None, height=dp(52),
                                 background_normal="", background_color=(0.95, 0.71, 0.14, 1),
                                 color=(0.11, 0.14, 0.2, 1))
            add.bind(on_release=lambda *a: self.show_add_form(p.get("code", "")))
            box.add_widget(add)

        if s is not None and s < 9.0 and not p.get("local"):
            alt = Factory.Button(text="ΒΡΕΣ ΚΑΛΥΤΕΡΗ ΕΝΑΛΛΑΚΤΙΚΗ", bold=True, size_hint_y=None, height=dp(52),
                                 background_normal="", background_color=(0.06, 0.48, 0.31, 1))
            alt_box = BoxLayout(orientation="vertical", size_hint_y=None)
            alt_box.bind(minimum_height=alt_box.setter("height"))
            alt.bind(on_release=lambda *a: self._alternatives(p, alt_box, alt))
            box.add_widget(alt)
            box.add_widget(alt_box)

        table = F.nutrition_table(p)
        if table:
            lights = {lbl: lv for lbl, v, lv in F.nutrient_lights(p)}
            lines = []
            for lbl, v, unit in table:
                key = lbl.strip().capitalize().replace("Κορεσμένα", "Κορεσμένα λιπαρά").replace("Σάκχαρα", "Ζάχαρη")
                lv = lights.get(key)
                tag = f"  [color={LIGHT[lv]}]{lv}[/color]" if lv else ""
                val = f"{v:.0f}" if unit == "kcal" else gr(v)
                lines.append(f"{esc(lbl)}: [b]{val} {unit}[/b]{tag}")
            serving = f" · μερίδα {esc(p['serving_size'])}" if p.get("serving_size") else ""
            box.add_widget(T(text=f"[b]Διατροφική αξία ανά 100 g/ml[/b]{serving}\n" + "\n".join(lines)))

        ingr = F.ingredients_text(p)
        if ingr:
            box.add_widget(T(text="[b]Συστατικά[/b]\n" + esc(ingr[:900]) + ("…" if len(ingr) > 900 else "")))
        al, tr = F.allergens(p)
        if al or tr:
            t = "[b]Αλλεργιογόνα[/b]"
            if al:
                t += "\n[color=#B4461B][b]Περιέχει: " + ", ".join(esc(x) for x in al) + "[/b][/color]"
            if tr:
                t += "\nΜπορεί να περιέχει ίχνη: " + ", ".join(esc(x) for x in tr)
            box.add_widget(T(text=t))
        adds = F.additives_named(p)
        if adds:
            lines = []
            for code, name, bad in adds:
                txt = f"{code}" + (f" – {esc(name)}" if name else "")
                lines.append(f"[color=#B4461B]{txt} (καλύτερα να αποφεύγεται)[/color]" if bad else txt)
            box.add_widget(T(text="[b]Πρόσθετα[/b]\n" + "\n".join("• " + x for x in lines)))
        org = F.origin(p)
        extra = org + ([f"Συσκευασία: {p['packaging']}"] if p.get("packaging") else [])
        if extra:
            box.add_widget(T(text="[b]Προέλευση και συσκευασία[/b]\n" + "\n".join(esc(x) for x in extra)))

        box.add_widget(T(text=f"[size=12sp][color={GREY}]Ο βαθμός αφορά τη διατροφική ποιότητα "
                              "(Nutri-Score, επεξεργασία, πρόσθετα), όχι τη γεύση ή τη φρεσκάδα. "
                              f"Στοιχεία: {'δική σου καταχώριση' if p.get('local') else 'Open Food Facts'} · κωδικός "
                              f"{esc(p.get('code', ''))}[/color][/size]"))
        self._price_section(box, p)
        cmp_btn = Factory.Button(text="ΠΡΟΣΘΗΚΗ ΣΤΗ ΣΥΓΚΡΙΣΗ", bold=True, size_hint_y=None, height=dp(54),
                                 background_normal="", background_color=(0.36, 0.25, 0.6, 1))

        def to_compare(*a):
            lst = H.add_compare(p)
            if len(lst) >= 2:
                self.go("compare")
            else:
                cmp_btn.text = "Προστέθηκε. Σκάναρε ή διάλεξε το 2ο προϊόν"
        cmp_btn.bind(on_release=to_compare)
        box.add_widget(cmp_btn)
        b1 = Factory.Button(text="ΔΕΣ ΤΙΜΕΣ ΣΤΟ E-KATANALOTIS", bold=True, size_hint_y=None, height=dp(54),
                            background_normal="", background_color=(0.15, 0.39, 0.79, 1))
        b1.bind(on_release=lambda *a: self.prices(p))
        b2 = Factory.Button(text="ΣΚΑΝΑΡΙΣΜΑ ΑΛΛΟΥ ΠΡΟΪΟΝΤΟΣ", bold=True, size_hint_y=None, height=dp(54),
                            background_normal="", background_color=(0.95, 0.71, 0.14, 1), color=(0.11, 0.14, 0.2, 1))
        b2.bind(on_release=lambda *a: self.go("scan"))
        box.add_widget(b1)
        box.add_widget(b2)
        self.root_w.ids.sm.current = "result"
        self._set_camera(False)

    def _alternatives(self, p, alt_box, btn):
        from kivy.factory import Factory
        btn.disabled = True
        btn.text = "Αναζήτηση εναλλακτικών…"

        def work():
            try:
                res = F.alternatives(p)
            except Exception:  # noqa: BLE001
                res = []
            Clock.schedule_once(lambda dt: done(res))

        def done(res):
            btn.text = "ΚΑΛΥΤΕΡΕΣ ΕΝΑΛΛΑΚΤΙΚΕΣ" if res else "Δεν βρέθηκε καλύτερο προϊόν στην ίδια κατηγορία"
            alt_box.clear_widgets()
            for sc, x in res:
                r = Row(text=f"[b]{esc(F.name_of(x))}[/b]\n[size=13sp][color={GREY}]{F.verdict(sc)}[/color][/size]",
                        badge=score_color(sc), score_text=gr(sc))
                r.bind(on_release=lambda w, prod=x: self.show_result(prod))
                alt_box.add_widget(r)

        threading.Thread(target=work, daemon=True).start()

    # ------------------------------------------------------------ προφίλ υγείας
    def show_profile(self):
        from kivy.factory import Factory
        self._set_camera(False)
        box = self.root_w.ids.profile_box
        box.clear_widgets()
        prof = H.load_profile()
        box.add_widget(Factory.Txt(text="[size=18sp][b]Το προφίλ υγείας μου[/b][/size]\nΤσέκαρε ό,τι σε αφορά. "
                                        "Όταν σκανάρεις κάτι ακατάλληλο, θα δεις κόκκινη ειδοποίηση και το κινητό "
                                        "θα δονηθεί."))
        checks = {}

        def row(key, label):
            r = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
            cb = Factory.CheckBox(active=key in prof.get("allergens", []) + prof.get("diets", []),
                                  size_hint_x=None, width=dp(46), color=(0.11, 0.14, 0.2, 1))
            r.add_widget(cb)
            r.add_widget(Label(text=label, color=(0.11, 0.14, 0.2, 1), halign="left", valign="middle",
                               text_size=(Window.width - dp(90), None)))
            box.add_widget(r)
            checks[key] = cb

        box.add_widget(Factory.Txt(text="[b]Αλλεργίες[/b]"))
        for k in H.ALLERGEN_KEYS:
            row(k, F.ALLERGENS.get(k, k))
        box.add_widget(Factory.Txt(text="[b]Διατροφή και υγεία[/b]"))
        for k, label in H.DIETS:
            row(k, label)

        def save(*a):
            H.save_profile({"allergens": [k for k in H.ALLERGEN_KEYS if checks[k].active],
                            "diets": [k for k, _ in H.DIETS if checks[k].active]})
            btn.text = "ΑΠΟΘΗΚΕΥΤΗΚΕ"
            Clock.schedule_once(lambda dt: self.go("scan"), 0.8)
        btn = Factory.Button(text="ΑΠΟΘΗΚΕΥΣΗ ΠΡΟΦΙΛ", bold=True, size_hint_y=None, height=dp(54),
                             background_normal="", background_color=(0.95, 0.71, 0.14, 1), color=(0.11, 0.14, 0.2, 1))
        btn.bind(on_release=save)
        box.add_widget(btn)
        box.add_widget(Factory.Txt(text=f"[size=12sp][color={GREY}]Οι ειδοποιήσεις βασίζονται στα στοιχεία της "
                                        "βάσης και στα συστατικά. Για σοβαρή αλλεργία διάβαζε πάντα και την ετικέτα "
                                        "της συσκευασίας. Τα όρια ζάχαρης, αλατιού και κορεσμένων είναι τα γενικά "
                                        "όρια «υψηλής» περιεκτικότητας ανά 100 g και δεν αντικαθιστούν τις οδηγίες "
                                        "του γιατρού σου.[/color][/size]"))
        self.root_w.ids.sm.current = "profile"
        for nid in ("nav_scan", "nav_search", "nav_hist", "nav_prices", "nav_compare"):
            self.root_w.ids[nid].state = "normal"

    def _vibrate(self):
        if not IS_ANDROID:
            return
        try:
            from jnius import autoclass
            act = autoclass("org.kivy.android.PythonActivity").mActivity
            Context = autoclass("android.content.Context")
            act.getSystemService(Context.VIBRATOR_SERVICE).vibrate(500)
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------ σύγκριση
    def show_compare(self):
        from kivy.factory import Factory
        box = self.root_w.ids.compare_box
        box.clear_widgets()
        lst = H.load_compare()
        if len(lst) < 2:
            box.add_widget(Factory.Txt(text="[size=17sp][b]Σύγκριση δύο προϊόντων[/b][/size]\n"
                                            + ("Έχεις διαλέξει 1 προϊόν: " + esc(F.name_of(lst[0])) + ".\n" if lst else "")
                                            + "Άνοιξε ένα προϊόν (σκανάρισμα, αναζήτηση ή ιστορικό) και πάτα "
                                              "«ΠΡΟΣΘΗΚΗ ΣΤΗ ΣΥΓΚΡΙΣΗ». Μόλις έχεις δύο, εμφανίζονται εδώ "
                                              "δίπλα-δίπλα."))
            return
        a, b = lst[0], lst[1]
        box.add_widget(Factory.Txt(text=f"[b]Α:[/b] {esc(F.name_of(a))}\n[b]Β:[/b] {esc(F.name_of(b))}"))
        v = H.verdict(a, b)
        if v:
            box.add_widget(Banner(text=f"[size=16sp][b]{esc(v)}[/b][/size]", bg=[0.06, 0.48, 0.31, 1]))
        from kivy.uix.gridlayout import GridLayout
        grid = GridLayout(cols=3, size_hint_y=None, spacing=dp(2), row_default_height=dp(40),
                          row_force_default=True)
        grid.bind(minimum_height=grid.setter("height"))

        def cell(text, win=False, head=False):
            lbl = Factory.Cell(text=text, bg=[0.82, 0.93, 0.85, 1] if win else ([0.86, 0.87, 0.9, 1] if head
                                                                               else [1, 1, 1, 1]))
            grid.add_widget(lbl)

        cell("[b]Στοιχείο[/b]", head=True)
        cell("[b]Α[/b]", head=True)
        cell("[b]Β[/b]", head=True)
        for label, ta, tb, win in H.compare_rows(a, b):
            cell(esc(label))
            cell(("[b]" + esc(ta) + "[/b]") if win == "a" else esc(ta), win == "a")
            cell(("[b]" + esc(tb) + "[/b]") if win == "b" else esc(tb), win == "b")
        box.add_widget(grid)
        for tag, p in (("Α", a), ("Β", b)):
            al = H.check(p)
            if al:
                lvl = H.worst(al)
                box.add_widget(Banner(text=f"[b]{tag}: {'ακατάλληλο για σένα' if lvl == 'red' else 'προσοχή'}[/b]\n"
                                           + "\n".join("• " + esc(m) for _, m in al), bg=ALERT_BG[lvl]))
        box.add_widget(Factory.Txt(text=f"[size=12sp][color={GREY}]Πράσινο = καλύτερο. Η τιμή ανά κιλό/λίτρο "
                                        "υπολογίζεται από τη φθηνότερη τιμή που έχεις καταγράψει και την ποσότητα "
                                        "της συσκευασίας.[/color][/size]"))
        for tag, p in (("Α", a), ("Β", b)):
            bt = Factory.Button(text=f"Άνοιγμα {tag}", size_hint_y=None, height=dp(46))
            bt.bind(on_release=lambda w, prod=p: self.show_result(prod, record=False))
            box.add_widget(bt)
        clr = Factory.Button(text="ΝΕΑ ΣΥΓΚΡΙΣΗ", bold=True, size_hint_y=None, height=dp(50), background_normal="",
                             background_color=(0.36, 0.25, 0.6, 1))
        clr.bind(on_release=lambda *x: (H.clear_compare(), self.show_compare()))
        box.add_widget(clr)

    # ------------------------------------------------------------ τιμές
    def _price_section(self, box, p):
        from kivy.factory import Factory
        region = F.get_setting("region", "")
        rows = F.prices_for(p.get("code"))
        txt = "[b]Τιμές που έχεις καταγράψει[/b]"
        if rows:
            best = rows[0]["price"]
            for r in rows:
                star = " [color=#0F7B4F][b]← φθηνότερο[/b][/color]" if r["price"] == best else ""
                pu = H.per_unit(r["price"], p)
                unit = f" · {euro(pu[0])}/{'κιλό' if pu[1] == 'kg' else 'λίτρο'}" if pu else ""
                txt += (f"\n• {esc(r['store'])}{' – ' + esc(r['region']) if r.get('region') else ''}: "
                        f"[b]{euro(r['price'])}[/b]{unit} [size=12sp]({r['date']})[/size]{star}")
        else:
            txt += "\nΚαμία ακόμα. Γράψε την τιμή που βλέπεις στο ράφι ή στο e-katanalotis."
        box.add_widget(Factory.Txt(text=txt))
        row1 = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6), padding=(dp(8), 0))
        store = Factory.Spinner(text=F.get_setting("store", F.STORES[0]), values=F.STORES, size_hint_x=0.55)
        reg = Factory.TextInput(text=region, hint_text="Περιοχή", multiline=False, size_hint_x=0.45)
        row1.add_widget(store)
        row1.add_widget(reg)
        row2 = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6), padding=(dp(8), 0))
        price = Factory.TextInput(hint_text="Τιμή €", input_filter="float", multiline=False, size_hint_x=0.45)
        save = Factory.Button(text="ΑΠΟΘΗΚΕΥΣΗ ΤΙΜΗΣ", bold=True, background_normal="",
                              background_color=(0.06, 0.48, 0.31, 1), size_hint_x=0.55)

        def do_save(*a):
            try:
                v = float(price.text.replace(",", "."))
            except ValueError:
                return
            F.set_setting("store", store.text)
            F.set_setting("region", reg.text.strip())
            F.add_price(p, store.text, reg.text.strip(), v)
            self.show_result(p, record=False)
        save.bind(on_release=do_save)
        row2.add_widget(price)
        row2.add_widget(save)
        box.add_widget(row1)
        box.add_widget(row2)

    def show_prices(self):
        from kivy.factory import Factory
        ids = self.root_w.ids
        regs = ["Όλες"] + F.regions()
        ids.region_filter.values = regs
        if ids.region_filter.text not in regs:
            ids.region_filter.text = "Όλες"
        lst = ids.price_list
        lst.clear_widgets()
        data = F.cheapest_by_category(ids.region_filter.text)
        if not data:
            lst.add_widget(Factory.Txt(text="Δεν έχεις καταγράψει ακόμα τιμές. Σκάναρε ένα προϊόν και, στο "
                                            "αποτέλεσμα, γράψε κατάστημα, περιοχή και τιμή."))
            return
        lst.add_widget(Factory.Txt(text="[b]Φθηνότερο κατάστημα ανά προϊόν και κατηγορία[/b]\n"
                                        f"[size=12sp][color={GREY}]Από τις τιμές που έχεις καταγράψει. "
                                        "Πάτα ένα προϊόν για λεπτομέρειες.[/color][/size]"))
        for cat in F.CATEGORIES:
            if cat not in data:
                continue
            lst.add_widget(Factory.Txt(text=f"[size=16sp][b]{esc(cat)}[/b][/size]"))
            for rec, n in data[cat]:
                s = rec.get("score")
                r = Row(text=f"[b]{esc(rec['name'])}[/b]\n[color=#0F7B4F][b]{euro(rec['price'])}[/b][/color] "
                             f"στο {esc(rec['store'])}{' – ' + esc(rec['region']) if rec.get('region') else ''}"
                             f"\n[size=12sp][color={GREY}]{n} καταγραφές · {rec['date']}[/color][/size]",
                        badge=score_color(s), score_text=gr(s) if s is not None else "–", code=rec["code"])
                r.bind(on_release=lambda w: self.lookup(w.code))
                lst.add_widget(r)

    # ------------------------------------------------------------ προσθήκη προϊόντος
    def show_add_form(self, code):
        from kivy.factory import Factory
        box = self.root_w.ids.add_box
        box.clear_widgets()
        self._set_camera(False)
        box.add_widget(Factory.Txt(text=f"[size=17sp][b]Το προϊόν δεν βρέθηκε[/b][/size]\nΚωδικός {code}. "
                                        "Πρόσθεσέ το από τη διατροφική ετικέτα της συσκευασίας (ανά 100 g ή "
                                        "100 ml). Ο βαθμός υπολογίζεται αυτόματα και θα το βρίσκεις κάθε φορά "
                                        "που το σκανάρεις."))
        f = {}

        def field(key, label, numeric=False, hint=""):
            row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
            row.add_widget(Label(text=label, color=(0.11, 0.14, 0.2, 1), halign="left", valign="middle",
                                 text_size=(Window.width * 0.45, None), size_hint_x=0.5))
            ti = Factory.TextInput(multiline=False, hint_text=hint, size_hint_x=0.5,
                                   input_filter="float" if numeric else None)
            row.add_widget(ti)
            box.add_widget(row)
            f[key] = ti

        def choice(key, label, values, default):
            row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
            row.add_widget(Label(text=label, color=(0.11, 0.14, 0.2, 1), halign="left", valign="middle",
                                 text_size=(Window.width * 0.45, None), size_hint_x=0.5))
            sp = Factory.Spinner(text=default, values=values, size_hint_x=0.5)
            row.add_widget(sp)
            box.add_widget(row)
            f[key] = sp

        field("name", "Όνομα προϊόντος", hint="π.χ. Φέτα ΠΟΠ")
        field("brand", "Μάρκα")
        field("qty", "Ποσότητα", hint="π.χ. 400 g")
        choice("cat", "Κατηγορία", F.CATEGORIES, "Άλλο")
        choice("bev", "Είναι ρόφημα;", ["Όχι", "Ναι"], "Όχι")
        field("kcal", "Ενέργεια (kcal)", True)
        field("sugars", "Σάκχαρα (g)", True)
        field("sat", "Κορεσμένα λιπαρά (g)", True)
        field("salt", "Αλάτι (g)", True)
        field("fiber", "Φυτικές ίνες (g)", True, "αν γράφει")
        field("protein", "Πρωτεΐνες (g)", True)
        field("fruit", "Φρούτα/λαχανικά/ξηροί καρποί (%)", True, "συνήθως 0")
        nova_vals = ["1 – ανεπεξέργαστο (γάλα, όσπρια)", "2 – υλικό μαγειρικής (λάδι, αλάτι)",
                     "3 – επεξεργασμένο (τυρί, ψωμί, κονσέρβα)", "4 – υπερεπεξεργασμένο (αναψυκτικό, γαριδάκι)"]
        choice("nova", "Επεξεργασία", nova_vals, nova_vals[2])
        field("adds", "Πρόσθετα (E-κωδικοί)", hint="π.χ. E330, E250")
        msg = Factory.Txt(text="")

        def num(k):
            try:
                return float(f[k].text.replace(",", ".") or 0)
            except ValueError:
                return 0.0

        def save(*a):
            if not f["name"].text.strip() or not f["kcal"].text.strip():
                msg.text = "[color=#B4461B]Συμπλήρωσε τουλάχιστον όνομα και ενέργεια.[/color]"
                return
            p = F.save_local_product(code, f["name"].text.strip(), f["brand"].text.strip(), f["qty"].text.strip(),
                                     f["cat"].text, f["bev"].text == "Ναι", num("kcal"), num("sugars"), num("sat"),
                                     num("salt"), num("fiber"), num("protein"), num("fruit"),
                                     int(f["nova"].text[0]), f["adds"].text)
            self.show_result(p)

        b = Factory.Button(text="ΑΠΟΘΗΚΕΥΣΗ ΚΑΙ ΒΑΘΜΟΣ", bold=True, size_hint_y=None, height=dp(54),
                           background_normal="", background_color=(0.95, 0.71, 0.14, 1), color=(0.11, 0.14, 0.2, 1))
        b.bind(on_release=save)
        box.add_widget(msg)
        box.add_widget(b)
        off = Factory.Button(text="Πρόσθεσέ το και στο Open Food Facts (για όλους)", size_hint_y=None,
                             height=dp(48), background_normal="", background_color=(0.15, 0.39, 0.79, 1))
        off.bind(on_release=lambda *a: webbrowser.open(F.off_add_url(code)))
        box.add_widget(off)
        back = Factory.Button(text="Άκυρο", size_hint_y=None, height=dp(46))
        back.bind(on_release=lambda *a: self.go("scan"))
        box.add_widget(back)
        self.root_w.ids.sm.current = "add"

    def prices(self, p):
        try:
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(F.name_of(p))
        except Exception:  # noqa: BLE001
            pass
        webbrowser.open(F.EKATANALOTIS)

    # ------------------------------------------------------------ αναζήτηση με όνομα
    def do_search(self, term):
        term = term.strip()
        if not term or self.busy:
            return
        self.busy = True
        lst = self.root_w.ids.search_list
        lst.clear_widgets()
        from kivy.factory import Factory
        lst.add_widget(Factory.Txt(text=f"Αναζήτηση «{esc(term)}»…"))

        def work():
            try:
                res = F.search(term)
                if not res:
                    res = F.search(term, greece_only=False)
                err = None
            except Exception as e:  # noqa: BLE001
                res, err = [], str(e)[:100]
            Clock.schedule_once(lambda dt: self._search_done(term, res, err))

        threading.Thread(target=work, daemon=True).start()

    def _search_done(self, term, res, err):
        self.busy = False
        from kivy.factory import Factory
        lst = self.root_w.ids.search_list
        lst.clear_widgets()
        if err:
            lst.add_widget(Factory.Txt(text=f"Σφάλμα αναζήτησης: {esc(err)}"))
            return
        scored = [(F.score(p)[0], p) for p in res]
        scored.sort(key=lambda sp: -(sp[0] if sp[0] is not None else -1))
        lst.add_widget(Factory.Txt(text=f"[b]{len(scored)} προϊόντα για «{esc(term)}»[/b] · το καλύτερο πρώτο. "
                                        "Πάτα ένα για λεπτομέρειες."))
        for s, p in scored:
            lv = H.worst(H.check(p))
            mark = ("  [color=#B4461B][b]ακατάλληλο για σένα[/b][/color]" if lv == "red" else
                    ("  [color=#C98A00][b]προσοχή[/b][/color]" if lv == "orange" else ""))
            r = Row(text=f"[b]{esc(F.name_of(p))}[/b]\n[size=13sp][color={GREY}]{F.verdict(s)}[/color][/size]{mark}",
                    badge=score_color(s), score_text=gr(s) if s is not None else "–")
            r.bind(on_release=lambda w, prod=p: self.show_result(prod))
            lst.add_widget(r)

    # ------------------------------------------------------------ ιστορικό
    def show_history(self):
        from kivy.factory import Factory
        lst = self.root_w.ids.hist_list
        lst.clear_widgets()
        h = F.load_history()
        lst.add_widget(Factory.Txt(text="[b]Προϊόντα που έλεγξες[/b]" if h else
                                   "Δεν έχεις ελέγξει ακόμα κανένα προϊόν."))
        for it in h:
            s = it.get("score")
            r = Row(text=f"[b]{esc(it['name'])}[/b]\n[size=13sp][color={GREY}]{F.verdict(s)} · {it['when']}"
                         f"[/color][/size]", badge=score_color(s), score_text=gr(s) if s is not None else "–",
                    code=it.get("code") or "")
            r.bind(on_release=lambda w: self.lookup(w.code))
            lst.add_widget(r)


if __name__ == "__main__":
    PoiotitaApp().run()
