import sys
import json
import time

import pygraphviz as pgv
from PIL import Image
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget, QFileDialog, QGraphicsView, QGraphicsScene,
    QInputDialog, QMessageBox
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt


class Ball:
    def __init__(self, num_stripes):
        self.num_stripes = num_stripes
        self.colors = ["Blue", "Yellow", "Green"]
        self.stripes = [None] * num_stripes

    def color_stripes(self):
        i = 0
        j = 0
        l = len(self.colors)
        for stripe in range(self.num_stripes):
            colors = []
            while j < l - 2:
                colors.append(self.colors[i % l])
                i += 1
                j += 1
            j = 0
            colors.append(self.colors[i % l])
            i -= 1
            colors.append(self.colors[i % l])
            i += 1
            self.stripes[stripe] = colors

    def __str__(self):
        output = ""
        for stripe, colors in enumerate(self.stripes):
            output += f"Sector {stripe + 1}:\n"
            output += ", ".join(colors) + ".\n"
        return output


class ResizableGraphicsView(QGraphicsView):
    def resizeEvent(self, event):
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
        super().resizeEvent(event)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setup_ui()
        self.data = None
        self.setWindowTitle("PeaceDoBall")
        self.ball = None

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.btn_open = QPushButton('Open JSON file')
        self.btn_open.clicked.connect(self.open_file)

        self.btn_manual_input = QPushButton('Manual input')
        self.btn_manual_input.clicked.connect(self.manual_input)

        self.btn_solve = QPushButton('Solve')
        self.btn_solve.clicked.connect(self.solve_problem)

        self.text_edit = QTextEdit()

        self.graph_view = ResizableGraphicsView()
        self.scene = QGraphicsScene()
        self.graph_view.setScene(self.scene)

        self.layout.addWidget(self.btn_open)
        self.layout.addWidget(self.btn_manual_input)
        self.layout.addWidget(self.btn_solve)
        self.layout.addWidget(self.text_edit)
        self.layout.addWidget(self.graph_view)
        # Set initial window geometry
        self.setGeometry(750, 750, 800, 600)  # x, y, width, height

    def generate_graph(self):
        if self.data is None:
            self.show_warning()
            return

        if self.ball is None or self.ball.num_stripes != self.data['num_stripes']:
            self.ball = Ball(self.data['num_stripes'])
            self.ball.color_stripes()

        G = pgv.AGraph(directed=True)

        # Add stripes as nodes to the graph, naming them with both the stripe index and color
        for i, stripe in enumerate(self.ball.stripes):
            for j, color in enumerate(stripe):
                G.add_node(f"{color} ({i + 1}, {j + 1})", fillcolor=color.lower(), style='filled')

        # Connect the first color of the stripe to the rest colors
        for i, stripe in enumerate(self.ball.stripes):
            for j, color in enumerate(stripe[1:], start=1):
                G.add_edge(f"{stripe[0]} ({i + 1}, 1)", f"{color} ({i + 1}, {j + 1})")

        width = self.graph_view.width() / 70
        height = self.graph_view.height() / 70
        G.graph_attr.update(size=f"{width},{height}!")

        G.layout(prog='dot')

        G.draw('graph.png')

        img = Image.open('graph.png')
        qim = QImage(img.tobytes('raw', 'RGBA'), img.size[0], img.size[1], QImage.Format_ARGB32)
        pix = QPixmap.fromImage(qim)

        self.scene.clear()
        self.scene.addPixmap(pix)
        self.graph_view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def open_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open JSON file", "", "JSON Files (*.json)", options=options
        )
        if file_name:
            try:
                with open(file_name, 'r') as f:
                    self.data = json.load(f)
                self.text_edit.setText(json.dumps(self.data, indent=4))
            except Exception as e:
                QMessageBox.warning(self, 'Warning', f'Failed to open or read file. Error: {str(e)}')

    def manual_input(self):
        num_stripes, ok = QInputDialog.getInt(
            self, 'Input', 'Enter the number of stripes:', min=0, max=200
        )
        if ok:
            self.data = {'num_stripes': num_stripes}
            self.text_edit.setText(json.dumps(self.data, indent=4))

    def solve_problem(self):
        if self.data is None:
            self.show_warning()
            return

        start_time = time.time()
        self.generate_graph()
        end_time = time.time()
        self.text_edit.setText(
            f'Time taken: {end_time - start_time} seconds\n{str(self.ball)}'
        )

    def show_warning(self):
        QMessageBox.warning(self, 'Warning', 'No data available. Please open a JSON file or input data manually.')


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
