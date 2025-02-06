import sys
import sqlite3
from datetime import datetime
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QTabWidget, QDateEdit, QMessageBox, QComboBox, QHeaderView
)

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('gestao_pessoal.db')
        self.criar_tabelas()
        self.inserir_dados_iniciais()

    def criar_tabelas(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Funcionarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cpf TEXT UNIQUE NOT NULL,
                cargo TEXT NOT NULL,
                departamento TEXT NOT NULL,
                data_contratacao DATE DEFAULT CURRENT_DATE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Folha_Pagamento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                funcionario_id INTEGER NOT NULL,
                mes INTEGER NOT NULL,
                ano INTEGER NOT NULL,
                salario_base REAL NOT NULL,
                horas_extras INTEGER DEFAULT 0,
                valor_hora_extra REAL DEFAULT 0,
                total_salario REAL NOT NULL,
                FOREIGN KEY (funcionario_id) REFERENCES Funcionarios (id),
                CONSTRAINT check_mes CHECK (mes BETWEEN 1 AND 12),
                CONSTRAINT check_ano CHECK (ano >= 2000),
                CONSTRAINT unique_folha UNIQUE (funcionario_id, mes, ano)
            )
        ''')
        self.conn.commit()

    def inserir_dados_iniciais(self):
        cursor = self.conn.cursor()
        # Check if there are any records
        cursor.execute('SELECT COUNT(*) FROM Funcionarios')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO Funcionarios (nome, cpf, cargo, departamento)
                VALUES 
                ('João Silva', '123.456.789-00', 'Analista', 'TI'),
                ('Maria Santos', '987.654.321-00', 'Gerente', 'RH')
            ''')
            
            # Insert initial payroll data
            cursor.execute('''
                INSERT INTO Folha_Pagamento (funcionario_id, mes, ano, salario_base, 
                                           horas_extras, valor_hora_extra, total_salario)
                VALUES 
                (1, 1, 2024, 5000.00, 10, 50.00, 5500.00),
                (2, 1, 2024, 7000.00, 5, 70.00, 7350.00)
            ''')
        self.conn.commit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.setup_ui()
        self.setup_styles()
        
    def setup_ui(self):
        self.setWindowTitle("Sistema de Gestão de Pessoal")
        self.setMinimumSize(800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Setup tabs
        self.setup_funcionarios_tab(tabs)
        self.setup_folha_tab(tabs)
        
        # Load initial data
        self.carregar_funcionarios()
        self.carregar_folha()
    
    def setup_styles(self):
        style = """
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #f6f7f9, stop:1 #e5e9f0);
        }
        QTabWidget::pane {
            border: 1px solid #d1d5db;
            border-radius: 5px;
            background: white;
        }
        QTabBar::tab {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #f8f9fa, stop:1 #e9ecef);
            border: 1px solid #d1d5db;
            padding: 8px 15px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background: white;
            border-bottom-color: white;
        }
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #0d6efd, stop:1 #0b5ed7);
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #0b5ed7, stop:1 #0a58ca);
        }
        QLineEdit, QComboBox, QDateEdit {
            padding: 6px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            background: white;
        }
        QTableWidget {
            background: white;
            gridline-color: #e9ecef;
            selection-background-color: #0d6efd;
            selection-color: white;
            border: 1px solid #dee2e6;
            border-radius: 4px;
        }
        QTableWidget::item {
            padding: 5px;
        }
        QHeaderView::section {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #f8f9fa, stop:1 #e9ecef);
            padding: 8px;
            border: none;
            border-right: 1px solid #dee2e6;
            border-bottom: 1px solid #dee2e6;
        }
    """
        self.setStyleSheet(style)

    def setup_funcionarios_tab(self, tabs):
        tab_funcionarios = QWidget()
        tabs.addTab(tab_funcionarios, "Funcionários")
        layout = QVBoxLayout(tab_funcionarios)
        
        # Formulário
        form_layout = QHBoxLayout()
        
        # Create input fields
        campos = [
            ('nome', 'Nome:'), 
            ('cpf', 'CPF:'),
            ('cargo', 'Cargo:'), 
            ('departamento', 'Departamento:')
        ]
        
        for campo, label in campos:
            group = QVBoxLayout()
            group.addWidget(QLabel(label))
            input_field = QLineEdit()
            setattr(self, f'input_{campo}', input_field)
            group.addWidget(input_field)
            form_layout.addLayout(group)
        
        # Botões
        botoes = QHBoxLayout()
        self.btn_salvar = QPushButton("Salvar")  # Make button a class attribute
        self.btn_salvar.clicked.connect(self.salvar_funcionario)
        self.btn_editar = QPushButton("Editar")
        self.btn_editar.clicked.connect(self.editar_funcionario)
        self.btn_excluir = QPushButton("Excluir")
        self.btn_excluir.clicked.connect(self.excluir_funcionario)
        
        botoes.addWidget(self.btn_salvar)
        botoes.addWidget(self.btn_editar)
        botoes.addWidget(self.btn_excluir)
        
        layout.addLayout(form_layout)
        layout.addLayout(botoes)
        
        # Tabela
        self.tabela_funcionarios = QTableWidget()
        self.tabela_funcionarios.setColumnCount(5)
        self.tabela_funcionarios.setHorizontalHeaderLabels([
            'ID', 'Nome', 'CPF', 'Cargo', 'Departamento'
        ])
        self.tabela_funcionarios.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabela_funcionarios)

    def setup_folha_tab(self, tabs):
        tab_folha = QWidget()
        tabs.addTab(tab_folha, "Folha de Pagamento")
        layout = QVBoxLayout(tab_folha)

        # Form layout
        form_layout = QVBoxLayout()
        
        # Funcionário select
        grupo_func = QHBoxLayout()
        label_func = QLabel("Funcionário:")
        self.combo_funcionarios = QComboBox()
        self.carregar_combo_funcionarios()
        grupo_func.addWidget(label_func)
        grupo_func.addWidget(self.combo_funcionarios)
        form_layout.addLayout(grupo_func)
        
        # Mês e Ano
        grupo_data = QHBoxLayout()
        label_mes = QLabel("Mês:")
        self.input_mes = QComboBox()
        self.input_mes.addItems([str(i) for i in range(1, 13)])
        label_ano = QLabel("Ano:")
        self.input_ano = QLineEdit()
        self.input_ano.setText(str(datetime.now().year))
        grupo_data.addWidget(label_mes)
        grupo_data.addWidget(self.input_mes)
        grupo_data.addWidget(label_ano)
        grupo_data.addWidget(self.input_ano)
        form_layout.addLayout(grupo_data)
        
        # Salário e extras
        grupo_salario = QHBoxLayout()
        label_base = QLabel("Salário Base:")
        self.input_salario_base = QLineEdit()
        label_horas = QLabel("Horas Extras:")
        self.input_horas_extras = QLineEdit()
        label_valor = QLabel("Valor Hora:")
        self.input_valor_hora = QLineEdit()
        grupo_salario.addWidget(label_base)
        grupo_salario.addWidget(self.input_salario_base)
        grupo_salario.addWidget(label_horas)
        grupo_salario.addWidget(self.input_horas_extras)
        grupo_salario.addWidget(label_valor)
        grupo_salario.addWidget(self.input_valor_hora)
        form_layout.addLayout(grupo_salario)

        # Botões
        botoes = QHBoxLayout()
        btn_salvar = QPushButton("Salvar Folha")
        btn_salvar.clicked.connect(self.salvar_folha)
        botoes.addWidget(btn_salvar)
        form_layout.addLayout(botoes)

        # Tabela
        self.tabela_folha = QTableWidget()
        self.tabela_folha.setColumnCount(8)
        self.tabela_folha.setHorizontalHeaderLabels([
            'ID', 'Funcionário', 'Mês', 'Ano', 
            'Salário Base', 'Horas Extras', 'Valor Hora', 'Total'
        ])
        self.tabela_folha.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addLayout(form_layout)
        layout.addWidget(self.tabela_folha)

    def carregar_combo_funcionarios(self):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute('SELECT id, nome FROM Funcionarios ORDER BY nome')
            self.combo_funcionarios.clear()
            for id_, nome in cursor.fetchall():
                self.combo_funcionarios.addItem(nome, id_)
        except sqlite3.Error as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao carregar funcionários: {str(e)}')

    def carregar_funcionarios(self):
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT id, nome, cpf, cargo, departamento, data_contratacao
            FROM Funcionarios''')
        dados = cursor.fetchall()
        
        self.tabela_funcionarios.setRowCount(len(dados))
        for row, (id_, nome, cpf, cargo, depto, data) in enumerate(dados):
            self.tabela_funcionarios.setItem(row, 0, QTableWidgetItem(str(id_)))
            self.tabela_funcionarios.setItem(row, 1, QTableWidgetItem(nome))
            self.tabela_funcionarios.setItem(row, 2, QTableWidgetItem(cpf))
            self.tabela_funcionarios.setItem(row, 3, QTableWidgetItem(cargo))
            self.tabela_funcionarios.setItem(row, 4, QTableWidgetItem(depto))
            self.tabela_funcionarios.setItem(row, 5, QTableWidgetItem(data))
        
        self.carregar_folha()

    def carregar_folha(self):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                SELECT 
                    fp.id,
                    f.nome,
                    fp.mes,
                    fp.ano,
                    fp.salario_base,
                    fp.horas_extras,
                    fp.valor_hora_extra,
                    fp.total_salario
                FROM Folha_Pagamento AS fp
                INNER JOIN Funcionarios AS f ON fp.funcionario_id = f.id
                ORDER BY fp.ano DESC, fp.mes DESC
            ''')
            
            self.tabela_folha.setRowCount(0)
            for row_data in cursor.fetchall():
                row = self.tabela_folha.rowCount()
                self.tabela_folha.insertRow(row)
                for column, data in enumerate(row_data):
                    item = QTableWidgetItem(str(data))
                    self.tabela_folha.setItem(row, column, item)
                    
        except sqlite3.Error as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao carregar folha de pagamento: {str(e)}')

    def salvar_funcionario(self):
        if hasattr(self, 'funcionario_em_edicao'):
            return self.atualizar_funcionario()
            
        dados = {
            'nome': self.input_nome.text(),
            'cpf': self.input_cpf.text(),
            'cargo': self.input_cargo.text(),
            'departamento': self.input_departamento.text()
        }
        
        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                INSERT INTO Funcionarios (nome, cpf, cargo, departamento)
                VALUES (?, ?, ?, ?)''',
                (dados['nome'], dados['cpf'], dados['cargo'], dados['departamento']))
            self.db.conn.commit()
            self.carregar_funcionarios()
            self.limpar_campos_funcionario()
            QMessageBox.information(self, "Sucesso", "Funcionário salvo com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {str(e)}")

    def editar_funcionario(self):
        # Get selected row
        selected_items = self.tabela_funcionarios.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, 'Aviso', 'Selecione um funcionário para editar.')
            return
        
        # Get the row number and data
        row = selected_items[0].row()
        funcionario_id = self.tabela_funcionarios.item(row, 0).text()
        
        # Get current values
        nome = self.tabela_funcionarios.item(row, 1).text()
        cpf = self.tabela_funcionarios.item(row, 2).text()
        cargo = self.tabela_funcionarios.item(row, 3).text()
        departamento = self.tabela_funcionarios.item(row, 4).text()
        
        # Populate input fields
        self.input_nome.setText(nome)
        self.input_cpf.setText(cpf)
        self.input_cargo.setText(cargo)
        self.input_departamento.setText(departamento)
        
        # Store the ID of the employee being edited
        self.funcionario_em_edicao = funcionario_id

        # Change button state
        self.btn_salvar.setText('Atualizar')
    
    def atualizar_funcionario(self):
        if not hasattr(self, 'funcionario_em_edicao'):
            return self.salvar_funcionario()
            
        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                UPDATE Funcionarios 
                SET nome = ?, cpf = ?, cargo = ?, departamento = ?
                WHERE id = ?
            ''', (
                self.input_nome.text(),
                self.input_cpf.text(),
                self.input_cargo.text(),
                self.input_departamento.text(),
                self.funcionario_em_edicao
            ))
            self.db.conn.commit()
            
            # Reset the form
            self.limpar_campos()
            self.carregar_funcionarios()
            self.btn_salvar.setText('Salvar')
            del self.funcionario_em_edicao
            
            QMessageBox.information(self, 'Sucesso', 'Funcionário atualizado com sucesso!')
        except sqlite3.Error as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao atualizar funcionário: {str(e)}')

    def limpar_campos(self):
        self.input_nome.clear()
        self.input_cpf.clear()
        self.input_cargo.clear()
        self.input_departamento.clear()

    def limpar_campos_funcionario(self):
        self.input_nome.clear()
        self.input_cpf.clear()
        self.input_cargo.clear()
        self.input_departamento.clear()

    def excluir_funcionario(self):
        # Get selected row
        selected_items = self.tabela_funcionarios.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, 'Aviso', 'Selecione um funcionário para excluir.')
            return
        
        # Confirm deletion
        reply = QMessageBox.question(self, 'Confirmar Exclusão', 
                                   'Tem certeza que deseja excluir este funcionário?',
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.No:
            return
            
        # Get the row and employee ID
        row = selected_items[0].row()
        funcionario_id = self.tabela_funcionarios.item(row, 0).text()
        
        try:
            # Delete from database
            cursor = self.db.conn.cursor()
            cursor.execute('DELETE FROM Funcionarios WHERE id = ?', (funcionario_id,))
            self.db.conn.commit()
            
            # Refresh table
            self.carregar_funcionarios()
            QMessageBox.information(self, 'Sucesso', 'Funcionário excluído com sucesso!')
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao excluir funcionário: {str(e)}')

    def salvar_folha(self):
        try:
            funcionario_id = self.combo_funcionarios.currentData()
            if not funcionario_id:
                QMessageBox.warning(self, 'Aviso', 'Selecione um funcionário.')
                return

            mes = int(self.input_mes.currentText())  # Changed from value()
            ano = int(self.input_ano.text())  # Changed from value()
            salario_base = float(self.input_salario_base.text() or 0)
            horas_extras = int(self.input_horas_extras.text() or 0)
            valor_hora = float(self.input_valor_hora.text() or 0)
            total_salario = self.calcular_salario(salario_base, horas_extras, valor_hora)

            cursor = self.db.conn.cursor()
            cursor.execute('''
                INSERT INTO Folha_Pagamento 
                (funcionario_id, mes, ano, salario_base, horas_extras, valor_hora_extra, total_salario)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (funcionario_id, mes, ano, salario_base, horas_extras, valor_hora, total_salario))
            
            self.db.conn.commit()
            self.carregar_folha()
            self.limpar_campos_folha()
            QMessageBox.information(self, 'Sucesso', 'Folha de pagamento registrada com sucesso!')
            
        except ValueError as e:
            QMessageBox.warning(self, 'Erro', 'Por favor, preencha todos os campos corretamente.')
        except sqlite3.Error as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao salvar folha de pagamento: {str(e)}')

    def calcular_salario(self, salario_base, horas_extras, valor_hora):
        return salario_base + (horas_extras * valor_hora)

    def limpar_campos_folha(self):
        self.combo_funcionarios.setCurrentIndex(0)
        self.input_mes.setCurrentText('1')  # Changed from setValue()
        self.input_ano.setText(str(QDate.currentDate().year()))  # Changed from setValue()
        self.input_salario_base.clear()
        self.input_horas_extras.clear()
        self.input_valor_hora.clear()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())