import requests
import urllib3
from datetime import datetime
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import StringProperty, ListProperty
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.pickers import MDDatePicker, MDTimePicker
from kivymd.uix.list import ThreeLineAvatarIconListItem, IconRightWidget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFillRoundFlatButton
from kivy.metrics import dp

# --- SSL ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURAÇÃO ---
API_BASE_URL = "https://tpe-server.onrender.com/api/registros"

DADOS_ZONAS = {
    "TV POA 2": ["6284_601_536", "6284_610_366"],
    "TV POA 3": ["6284_602_550", "6284_602_551", "6284_602_552", "6284_602_553", "6284_602_554", "6284_602_555", "6284_602_556"],
    "TV CXS": ["6284_603_591","6284_603_599","6284_603_584","6284_603_585","6284_603_586","6284_603_588","6284_603_589","6284_603_595","6284_603_597"],
    "TV PEL": ["6284_604_677", "6284_604_678", "6284_604_679", "6284_604_680", "6284_604_681", "6284_604_683", "6284_604_684", "6284_604_685", "6284_604_687", "6284_604_688", "6284_604_689", "6284_604_690", "6284_604_692", "6284_604_693", "6284_604_694"],
    "TV SMA": ["6284_605_660", "6284_605_661", "6284_605_663", "6284_605_664", "6284_605_666", "6284_605_667", "6284_605_668", "6284_605_669", "6284_605_672", "6284_605_678", "6284_605_680", "6284_605_681", "6284_605_682", "6284_605_683"],
    "TV PFD": ["6284_606_594", "6284_606_595", "6284_606_596", "6284_606_597", "6284_606_598", "6284_606_602", "6284_606_603", "6284_606_604", "6284_606_605", "6284_606_613", "6284_606_614", "6284_606_615", "6284_606_616"],
    "TV SCS": ["6284_608_561", "6284_608_567", "6284_608_568", "6284_608_569", "6284_608_577", "6284_608_579", "6284_608_580", "6284_608_581", "6284_608_582", "6284_608_584", "6284_608_585"],
    "TV CHA": ["6284_610_358", "6284_610_359", "6284_610_360", "6284_610_361", "6284_610_362", "6284_610_363", "6284_610_364", "6284_610_365", "6284_610_367", "6284_610_368", "6284_610_369", "6284_610_370", "6284_610_371"],
    "TV FLO": ["6284_612_310", "6284_612_307", "6284_612_311","6284_612_309"],
    "TV JOI": ["6284_613_319", "6284_613_328", "6284_613_329"]
}

MOTIVOS_LISTA = ["Falha no Sistema do SEFAZ", "Falha no Sistema Interno (BAT)", "Problema Mecânico com o Veículo", "Demora no redespacho", "Problema no cartão de abastecimento", "Outro"]

class DataManager:
    def _formatar_data(self, d_str, h_str):
        try:
            return datetime.strptime(f"{d_str} {h_str}", "%d/%m/%Y %H:%M").strftime("%Y-%m-%d %H:%M:%S")
        except:
            return None

    def adicionar(self, dados):
        # dados = (tv, zona, placa, motivo, outro, obs, status, d_ini, h_ini, d_fim, h_fim)
        motivo_final = dados[4] if dados[3] == "Outro" else dados[3]
        d_inicio = self._formatar_data(dados[7], dados[8]) or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        payload = {
            "tv": dados[0], "zona": dados[1], "placa_veiculo": dados[2],
            "motivo": motivo_final, "status": dados[6], "data_inicio": d_inicio
        }
        try:
            print("CRIANDO...", payload)
            res = requests.post(API_BASE_URL, json=payload, timeout=60, verify=False)
            return res.status_code == 201
        except Exception as e:
            print(f"Erro: {e}")
            return False

    def atualizar(self, id_reg, dados):
        # O mesmo de cima, mas inclui data fim
        motivo_final = dados[4] if dados[3] == "Outro" else dados[3]
        d_inicio = self._formatar_data(dados[7], dados[8])
        d_fim = self._formatar_data(dados[9], dados[10])

        payload = {
            "tv": dados[0], "zona": dados[1], "placa_veiculo": dados[2],
            "motivo": motivo_final, "status": dados[6], 
            "data_inicio": d_inicio, "data_fim": d_fim
        }
        try:
            print(f"ATUALIZANDO ID {id_reg}...", payload)
            res = requests.put(f"{API_BASE_URL}/{id_reg}", json=payload, timeout=60, verify=False)
            return res.status_code == 200
        except Exception as e:
            print(f"Erro: {e}")
            return False

    def buscar_todos(self, filtro_status=None):
        try:
            url = API_BASE_URL
            if filtro_status: url += f"?status={filtro_status}"
            
            res = requests.get(url, timeout=60, verify=False)
            if res.status_code == 200:
                lista_online = res.json()
                lista_formatada = []
                for item in lista_online:
                    # Função auxiliar para quebrar data em dia e hora
                    def parse_dt(dt_str):
                        try:
                            obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                            return obj.strftime("%d/%m/%Y"), obj.strftime("%H:%M")
                        except:
                            return "", ""

                    d_ini, h_ini = parse_dt(item.get('data_inicio', ''))
                    d_fim, h_fim = parse_dt(item.get('data_fim', ''))
                    duracao = item.get('duracao', '')

                    # ORDEM CORRIGIDA DA TUPLA:
                    # 0: id, 1: tv, 2: zona, 3: placa, 4: motivo, 5: outro, 6: obs, 
                    # 7: status, 8: d_ini, 9: h_ini, 10: d_fim, 11: h_fim, 12: duracao
                    reg = (
                        item['id'], item['tv'], item['zona'], item['placa_veiculo'],
                        item['motivo'], "", "", item['status'],
                        d_ini, h_ini, d_fim, h_fim, duracao
                    )
                    lista_formatada.append(reg)
                return lista_formatada
            return []
        except:
            return []

db = DataManager()

# --- KV LANGUAGE ---
KV = """
#:import hex kivy.utils.get_color_from_hex

<HomeScreen>:
    name: "home"
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "AjudaTPE"
            md_bg_color: hex("#001f3f")
            specific_text_color: 1, 1, 1, 1
        MDBoxLayout:
            orientation: "vertical"
            padding: "20dp"
            spacing: "20dp"
            adaptive_height: True
            pos_hint: {"center_x": .5, "center_y": .5}
            MDFillRoundFlatButton:
                text: "+ NOVO REGISTRO"
                font_size: "18sp"
                size_hint_x: 1
                height: "80dp"
                md_bg_color: hex("#0074D9")
                on_release: app.ir_para_formulario(novo=True)
            MDFillRoundFlatButton:
                text: "PENDENTES"
                size_hint_x: 1
                height: "60dp"
                md_bg_color: hex("#FF851B")
                on_release: app.ir_para_lista("Pendente")
            MDFillRoundFlatButton:
                text: "CONCLUÍDAS"
                size_hint_x: 1
                height: "60dp"
                md_bg_color: hex("#2ECC40")
                on_release: app.ir_para_lista("Concluído")
        Widget:

<ListScreen>:
    name: "lista"
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: root.titulo_lista
            left_action_items: [["arrow-left", lambda x: app.voltar_home()]]
            md_bg_color: hex("#001f3f")
            specific_text_color: 1, 1, 1, 1
        MDBoxLayout:
            size_hint_y: None
            height: "60dp"
            padding: "10dp"
            MDTextField:
                id: search_field
                hint_text: "Pesquisar..."
                on_text: root.filtrar_lista(self.text)
        RecycleView:
            id: rv
            viewclass: 'ItemLista'
            RecycleBoxLayout:
                default_size: None, dp(72)
                default_size_hint: 1, None
                size_hint_y: None
                height: self.minimum_height
                orientation: 'vertical'

<ItemLista>:
    text: root.texto_linha1
    secondary_text: root.texto_linha2
    tertiary_text: root.texto_linha3
    on_release: app.editar_registro(root.id_registro)
    IconRightWidget:
        icon: root.icone_status
        theme_text_color: "Custom"
        text_color: root.cor_status

<FormScreen>:
    name: "formulario"
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Registo de Parada"
            left_action_items: [["arrow-left", lambda x: app.voltar_home()]]
            md_bg_color: hex("#001f3f")
            specific_text_color: 1, 1, 1, 1
        ScrollView:
            MDBoxLayout:
                orientation: "vertical"
                padding: "20dp"
                spacing: "20dp"
                adaptive_height: True
                MDTextField:
                    id: input_tv
                    hint_text: "TV"
                    on_focus: if self.focus: root.abrir_menu_tv()
                MDTextField:
                    id: input_zona
                    hint_text: "Zona"
                    on_focus: if self.focus: root.abrir_menu_zona()
                    disabled: True
                MDTextField:
                    id: input_placa
                    hint_text: "Placa do Veículo"
                MDTextField:
                    id: input_motivo
                    hint_text: "Motivo"
                    on_focus: if self.focus: root.abrir_menu_motivo()
                MDTextField:
                    id: input_outro
                    hint_text: "Qual outro motivo?"
                    opacity: 0
                    disabled: True
                    size_hint_y: None
                    height: 0
                MDBoxLayout:
                    adaptive_height: True
                    spacing: "15dp"
                    MDTextField:
                        id: date_inicio
                        hint_text: "Data Início"
                        on_focus: if self.focus: root.abrir_data("inicio")
                    MDTextField:
                        id: time_inicio
                        hint_text: "Hora Início"
                        on_focus: if self.focus: root.abrir_hora("inicio")
                MDTextField:
                    id: input_obs
                    hint_text: "Observação"
                MDTextField:
                    id: input_status
                    hint_text: "Status"
                    on_focus: if self.focus: root.abrir_menu_status()
                MDBoxLayout:
                    id: box_fim
                    orientation: "vertical"
                    adaptive_height: True
                    spacing: "15dp"
                    opacity: 0
                    disabled: True
                    MDLabel:
                        text: "Fim da Parada"
                        theme_text_color: "Secondary"
                    MDBoxLayout:
                        adaptive_height: True
                        spacing: "15dp"
                        MDTextField:
                            id: date_fim
                            hint_text: "Data Fim"
                            on_focus: if self.focus: root.abrir_data("fim")
                        MDTextField:
                            id: time_fim
                            hint_text: "Hora Fim"
                            on_focus: if self.focus: root.abrir_hora("fim")
                MDFillRoundFlatButton:
                    id: btn_acao
                    text: "SALVAR"
                    size_hint_x: 1
                    height: "50dp"
                    md_bg_color: hex("#0074D9")
                    on_release: root.salvar()
"""

class ItemLista(ThreeLineAvatarIconListItem):
    id_registro = StringProperty()
    texto_linha1 = StringProperty()
    texto_linha2 = StringProperty()
    texto_linha3 = StringProperty()
    icone_status = StringProperty("circle")
    cor_status = ListProperty([0, 0, 0, 1])

class HomeScreen(MDScreen): pass
class ListScreen(MDScreen):
    titulo_lista = StringProperty("Lista")
    status_filtro = StringProperty(None)
    def carregar_dados(self):
        registros = db.buscar_todos(self.status_filtro)
        self.popular_lista(registros)
    def filtrar_lista(self, texto):
        registros = db.buscar_todos(self.status_filtro)
        lista = [r for r in registros if texto.upper() in r[3].upper() or texto.upper() in r[1].upper()]
        self.popular_lista(lista)
    def popular_lista(self, registros):
        data_items = []
        for r in registros:
            status = r[7]
            cor = [1, 0.5, 0, 1] if status == "Pendente" else [0.18, 0.8, 0.25, 1]
            icone = "clock-alert-outline" if status == "Pendente" else "check-circle"
            
            # EXIBE A DURAÇÃO NA LISTA
            duracao = r[12] if r[12] else ""
            linha1 = f"{r[3]} | Tempo: {duracao}" if duracao else r[3]

            data_items.append({
                "id_registro": str(r[0]),
                "texto_linha1": linha1,
                "texto_linha2": r[4],
                "texto_linha3": f"{r[1]} - {r[2]}",
                "icone_status": icone, "cor_status": cor
            })
        self.ids.rv.data = data_items

class FormScreen(MDScreen):
    id_atual = None
    menu_tv, menu_zona, menu_motivo, menu_status = None, None, None, None

    def on_enter(self):
        self.configurar_menus()
        if not self.id_atual:
            self.limpar_campos()
            now = datetime.now()
            self.ids.date_inicio.text = now.strftime("%d/%m/%Y")
            self.ids.time_inicio.text = now.strftime("%H:%M")
            self.set_status("Pendente")
            self.ids.btn_acao.text = "REGISTRAR OCORRÊNCIA"
        else:
            self.carregar_registro(self.id_atual)
            self.ids.btn_acao.text = "SALVAR ALTERAÇÕES"

    def limpar_campos(self):
        ids = self.ids
        ids.input_tv.text = ""
        ids.input_zona.text = ""
        ids.input_placa.text = ""
        ids.input_motivo.text = ""
        ids.input_outro.text = ""
        ids.input_obs.text = ""
        ids.input_status.text = "Pendente"
        ids.date_fim.text = ""
        ids.time_fim.text = ""

    def carregar_registro(self, id_reg):
        registros = db.buscar_todos()
        # Acha o registro pelo ID
        reg = next((r for r in registros if str(r[0]) == str(id_reg)), None)
        if reg:
            ids = self.ids
            # AQUI ESTAVA O ERRO DE ÍNDICE - AGORA ESTÁ CORRIGIDO
            ids.input_tv.text = reg[1]
            ids.input_zona.text = reg[2]
            ids.input_placa.text = reg[3]
            ids.input_motivo.text = reg[4]
            ids.input_outro.text = reg[5]
            ids.input_obs.text = reg[6]
            self.set_status(reg[7]) # Status correto
            ids.date_inicio.text = reg[8] # Data correta
            ids.time_inicio.text = reg[9]
            ids.date_fim.text = reg[10]
            ids.time_fim.text = reg[11]
            
            ids.input_zona.disabled = False
            if reg[1] in DADOS_ZONAS:
                items = [{"text": z, "viewclass": "OneLineListItem", "on_release": lambda x=z: self.set_zona(x)} for z in DADOS_ZONAS[reg[1]]]
                self.menu_zona = MDDropdownMenu(caller=ids.input_zona, items=items, width_mult=4)

    def salvar(self):
        ids = self.ids
        dados = (
            ids.input_tv.text, ids.input_zona.text, ids.input_placa.text,
            ids.input_motivo.text, ids.input_outro.text, ids.input_obs.text,
            ids.input_status.text, ids.date_inicio.text, ids.time_inicio.text,
            ids.date_fim.text, ids.time_fim.text
        )
        if not self.id_atual:
            res = db.adicionar(dados)
        else:
            res = db.atualizar(self.id_atual, dados) # USA O ID PARA NÃO DUPLICAR
        
        if res:
            MDApp.get_running_app().voltar_home()

    # --- Menus e Pickers ---
    def configuring_menus(self): pass # Stub
    def configurar_menus(self):
        self.menu_tv = MDDropdownMenu(caller=self.ids.input_tv, items=[{"text": k, "viewclass": "OneLineListItem", "on_release": lambda x=k: self.set_tv(x)} for k in DADOS_ZONAS.keys()], width_mult=4)
        self.menu_motivo = MDDropdownMenu(caller=self.ids.input_motivo, items=[{"text": m, "viewclass": "OneLineListItem", "on_release": lambda x=m: self.set_motivo(x)} for m in MOTIVOS_LISTA], width_mult=4)
        self.menu_status = MDDropdownMenu(caller=self.ids.input_status, items=[{"text": s, "viewclass": "OneLineListItem", "on_release": lambda x=s: self.set_status(x)} for s in ["Pendente", "Concluído"]], width_mult=3)

    def set_tv(self, txt):
        self.ids.input_tv.text = txt
        self.ids.input_zona.disabled = False
        self.menu_tv.dismiss()
        items = [{"text": z, "viewclass": "OneLineListItem", "on_release": lambda x=z: self.set_zona(x)} for z in DADOS_ZONAS.get(txt, [])]
        self.menu_zona = MDDropdownMenu(caller=self.ids.input_zona, items=items, width_mult=4)

    def set_zona(self, txt):
        self.ids.input_zona.text = txt
        self.menu_zona.dismiss()
    def set_motivo(self, txt):
        self.ids.input_motivo.text = txt
        self.menu_motivo.dismiss()
        is_outro = (txt == "Outro")
        self.ids.input_outro.opacity = 1 if is_outro else 0
        self.ids.input_outro.disabled = not is_outro
        self.ids.input_outro.height = dp(60) if is_outro else 0
    def set_status(self, txt):
        self.ids.input_status.text = txt
        self.menu_status.dismiss()
        is_concl = (txt == "Concluído")
        self.ids.box_fim.opacity = 1 if is_concl else 0
        self.ids.box_fim.disabled = not is_concl
        if is_concl and not self.ids.date_fim.text:
            now = datetime.now()
            self.ids.date_fim.text = now.strftime("%d/%m/%Y")
            self.ids.time_fim.text = now.strftime("%H:%M")

    def abrir_menu_tv(self): self.menu_tv.open()
    def abrir_menu_zona(self): 
        if self.menu_zona: self.menu_zona.open()
    def abrir_menu_motivo(self): self.menu_motivo.open()
    def abrir_menu_status(self): self.menu_status.open()
    
    def abrir_data(self, campo):
        try:
            MDDatePicker().bind(on_save=lambda i, v, r: self.set_dt(v, campo)).open()
        except: pass
    def set_dt(self, v, campo):
        if campo == "inicio": self.ids.date_inicio.text = v.strftime("%d/%m/%Y")
        else: self.ids.date_fim.text = v.strftime("%d/%m/%Y")
    def abrir_hora(self, campo):
        try:
            MDTimePicker().bind(on_save=lambda i, t: self.set_tm(t, campo)).open()
        except: pass
    def set_tm(self, t, campo):
        if campo == "inicio": self.ids.time_inicio.text = t.strftime("%H:%M")
        else: self.ids.time_fim.text = t.strftime("%H:%M")

class AjudaTPEApp(MDApp):
    def build(self):
        Builder.load_string(KV)
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.primary_hue = "800"
        self.theme_cls.theme_style = "Light"
        self.sm = MDScreenManager()
        self.sm.add_widget(HomeScreen(name="home"))
        self.sm.add_widget(ListScreen(name="lista"))
        self.sm.add_widget(FormScreen(name="formulario"))
        return self.sm
    def ir_para_lista(self, f):
        s = self.sm.get_screen("lista")
        s.titulo_lista = f"Paradas {f}s"
        s.status_filtro = f
        s.carregar_dados()
        self.sm.transition.direction = "left"
        self.sm.current = "lista"
    def ir_para_formulario(self, novo=True):
        s = self.sm.get_screen("formulario")
        s.id_atual = None if novo else s.id_atual
        if novo: s.limpar_campos(); s.on_enter()
        self.sm.transition.direction = "left"
        self.sm.current = "formulario"
    def editar_registro(self, id_reg):
        s = self.sm.get_screen("formulario")
        s.id_atual = id_reg
        self.sm.transition.direction = "left"
        self.sm.current = "formulario"
    def voltar_home(self):
        self.sm.transition.direction = "right"
        self.sm.current = "home"

if __name__ == "__main__":
    AjudaTPEApp().run()