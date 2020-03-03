import sys
from PyQt5.QtGui import * 
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import pydicom
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import random
import cv2
import numpy as np
import ctypes
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
user32 = ctypes.windll.user32

#recebe o tamanho da janela
screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
fig = plt.figure()

# configurando janela do recorte
class MainCrop(QMainWindow):
    def __init__(self, img, name, button):
        QMainWindow.__init__(self)
        self.button = button
        global imageC
        imageC = img
        self.title = name
        self.left = 10
        self.top = 10
        self.width = 1920
        self.height = 1080
        self.imageCrop = img
        global image
        image = plt.imshow(img, cmap='gray', aspect='auto')
        global fig
        fig = plt.figure()
        self.cropped = False
        self.setWindowTitle(self.title)
        #self.setGeometry(self.left, self.top, self.width, self.height)
        self.statusBar().showMessage('Ready')

        mainMenu = self.menuBar()
        mainMenu.setNativeMenuBar(False)
        fileMenu = mainMenu.addMenu('File')
        helpMenu = mainMenu.addMenu('Help')

        exitButton = QAction(QIcon('exit24.png'), 'Exit', self)
        exitButton.setShortcut('Ctrl+Q')
        exitButton.setStatusTip('Exit application')
        exitButton.triggered.connect(self.close)
        fileMenu.addAction(exitButton)
        widget = QWidget(self)
        self.setCentralWidget(widget)
        vlay = QGridLayout(widget)
        self.formGroupBox = QGroupBox("Phanton  ")
        size = QSize(400, 150)
        self.formGroupBox.setMaximumSize(size)
        self.formGroupBox.setAlignment(Qt.AlignTop)
        vlay.addWidget(self.formGroupBox, 0, 0)

        self.nameLabel = QLabel('Descricao:', self)
        self.line = QTextEdit(self)
        self.line.setFixedWidth(325)
        self.line.setFixedHeight(60)

        size = QSize(20, 40)
        layout = QGridLayout()
        layout.addWidget(self.nameLabel, 0, 0)
        layout.addWidget(self.line, 0, 1)
        pybutton = QPushButton('Cortar e exportar', self)
        pybutton.clicked.connect(self.clickMethod)
        size = QSize(150, 40)
        pybutton.setMinimumSize(size)
        size = QSize(250, 40)
        pybutton.setMaximumSize(size)
        layout.addWidget(pybutton, 1,2)

        self.cancelButton = QPushButton('Cancelar', self)
        size = QSize(150, 40)
        self.cancelButton.setMinimumSize(size)
        size = QSize(250, 40)
        self.cancelButton.setMaximumSize(size)
        layout.addWidget(self.cancelButton, 1,1)
        self.formGroupBox.setLayout(layout)

        self.formGroupBox = QGroupBox("Ajuda  ")
        size = QSize(400, 200)
        self.formGroupBox.setMaximumSize(size)
        vlay.addWidget(self.formGroupBox, 1, 0)
        layout = QGridLayout()
        self.help = QLabel('Primeiro passo: clicar na luneta;', self)
        layout.addWidget(self.help, 0, 0)
        self.help = QLabel('Segundo passo: definir a regiao de corte para o Phanton clicando e arrastando;', self)
        layout.addWidget(self.help, 1, 0)
        self.help = QLabel('Terceiro passo: descrever o phanton no espaco acima;', self)
        layout.addWidget(self.help, 2, 0)
        self.help = QLabel('Quarto passo: Clicar no botao \'Cortar e exportar\';', self)
        layout.addWidget(self.help, 3, 0)
        self.help = QLabel('', self)
        layout.addWidget(self.help, 4, 0)
        self.help = QLabel('Dica: Caso haja a necessidade de refazer o corte, clique no primeiro botao \n \'Home\' para dar zoom out.', self)
        layout.addWidget(self.help, 5, 0)
        self.help = QLabel('Dica: Havendo a necessidade de deletar ou cancelar o atual recorte, \n clique no botao "cancelar".', self)
        layout.addWidget(self.help, 6, 0)
        self.formGroupBox.setLayout(layout)

        m = WidgetPlot(self)
        vlay.addWidget(m,0,1, 10,1)

    # maximiza a janela
    def showIt(self, button):
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMinimizeButtonHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        self.showMaximized()
        self.cropped = False                

    # fecha a janela
    def closeIt(self):
        self.close()
        return

    # salva o recorte
    def clickMethod(self):
        #plt.savefig('logo.jpg',bbox_inches='tight',dpi=100)
        img = np.fromstring(plt.gcf().canvas.tostring_rgb(), dtype=np.uint8, sep='')
        img  = img.reshape(fig.canvas.get_width_height()[::-1] + (3,))

        img = cv2.cvtColor(img,cv2.COLOR_RGB2BGR)
        newX,newY = screensize[0]/10, img.shape[0]/float(img.shape[1]/(screensize[0]/10))
        imagesScale = cv2.resize(img, (int(newX), int(newY)))
        height, width, channel = imagesScale.shape
        bytesPerLine = 3 * width
        qImg = QImage(imagesScale.data, width, height, bytesPerLine, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qImg)
        ButtonIcon = QIcon(pixmap)
        self.button.setIcon(ButtonIcon)
        self.button.setIconSize(pixmap.rect().size())
        self.button.setText('')
        self.cropped = True
        self.closeIt()
        #cv2.imwrite('alinhada.jpg', img)

# define as classes para a area de trabalho da imagem
class WidgetPlot(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.setLayout(QVBoxLayout())
        self.canvas = PlotCanvas(self, width=5, height=4)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout().addWidget(self.canvas)
        self.layout().addWidget(self.toolbar)

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=10, height=10, dpi=100):
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot()        

    def plot(self):
        ax = self.figure.add_subplot(111)
        plt.imshow(imageC, cmap='gray')
        ax.axis('off') 
        self.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    img = 1
    mainWin = MainCrop(img, 'test')
    mainWin.show()
    sys.exit( app.exec_())