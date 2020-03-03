from __future__ import print_function
import sys
import cv2
import numpy as np
import pydicom
import ctypes
import matplotlib.pyplot as plt
from Anotacao import MainCrop
from PyQt5.QtGui import * 
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial
from PIL import Image, ImageQt
from skimage.morphology import disk, binary_erosion

#recebe o tamanho da janela
user32 = ctypes.windll.user32
screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

# Classe para definir objetos do tipo DICOM e diferenciar
# as suas classes, para facilitar o entendimento

#classe basica Dicom
class Dicom(object):
    def __init__(self, arqDicom):
        self._arquivo = arqDicom
        self._array = None
        self._arrayHQ = None
        self._image = None
        self._imageHQ = None
        self._h = None
    
    def setArquivo(self, arqDicom):
        self._arquivo = arqDicom
    
    def setArray(self, arrayPixel):
        self._array = arrayPixel

    def setImage(self, img):
        self._image = img

    def setArrayHQ(self, arrayPixel):
        self._arrayHQ = arrayPixel

    def setImageHQ(self, img):
        self._imageHQ = img

    def getArquivo(self):
        return self._arquivo
    
    def getArray(self):
        return self._array

    def getImage(self):
        return self._image

    def getArrayHQ(self):
        return self._arrayHQ

    def getImageHQ(self):
        return self._imageHQ

#classe para definir a primeira imagem que sera alinhada 
class DicomOrigin(Dicom):
    def __init__(self, arqDicom):
        super(DicomOrigin, self).__init__(arqDicom)

#classe para definir a segunda imagem de referencia
class DicomNoAligned(Dicom):
    def __init__(self, arqDicom):
        super(DicomNoAligned, self).__init__(arqDicom)

#classe para definir a imagem alinhada
class DicomAligned(object):
    def __init__(self):
        self._arquivo = None
        self._array = None
        self._arrayHQ = None
        self._image = None
        self._imageHQ = None
    
    def setArquivo(self, arqDicom):
        self._arquivo = arqDicom
    
    def setArray(self, arrayPixel):
        self._array = arrayPixel

    def setImage(self, img):
        self._image = img

    def setArrayHQ(self, arrayPixel):
        self._arrayHQ = arrayPixel

    def setImageHQ(self, img):
        self._imageHQ = img

    def getArquivo(self):
        return self._arquivo
    
    def getArray(self):
        return self._array

    def getImage(self):
        return self._image

    def getArrayHQ(self):
        return self._arrayHQ

    def getImageHQ(self):
        return self._imageHQ

# Widget para carregar as tres imagens principais da aplicacao
class QWidgetPhanton(QWidget):    
    def __init__(self, parent=None):
        super(QWidgetPhanton, self).__init__(parent)
        self.label = QLabel()
        self.root = QHBoxLayout()
        self.program = QVBoxLayout(self)
        self.initUI()
        self.imageCrop = None 

    def initUI(self):
        self.label.setText('Project: Image Registration - V1.0')
        self.label.setFixedWidth(screensize[0]/3-10)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet('border: gray; border-style:solid; border-width: 1px;')

        self.root.addWidget(self.label)
        
        self.program.addLayout(self.root)

        self.setWindowTitle('DICOM Files - Registration')

# Aciona recortes do phantom
class QPushButtonLabel(QPushButton):    
    def __init__(self, mainClass):
        super(QPushButtonLabel, self).__init__(mainClass)
        self.created = False
        self.id = None
        self.phanton = None
        self.windowName = None
        self.image = None
        self.cropped = False
        self.cancel = False
        self.mainClass = mainClass
        self.clicked.connect(partial(self.mainClass.setImage, self))

    def setMain(self, MainClass):
        self.mainClass = MainClass

#exibir uma lista 
class Window(QWidget):
    
    #inicializar variaveis
    def __init__(self):
        super(Window, self).__init__()
        self.mainClass = None
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_widget.setMaximumWidth(200)
        self.elementos_widget = QWidget()
        self.count = 0
        vbox = QVBoxLayout(self.scroll_widget)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(self.elementos_widget)
        vbox.addStretch()

        self.elementos = QGridLayout()
        self.elementos_widget.setLayout(self.elementos)
        self.scroll.setWidget(self.scroll_widget)

        self.buttonAdd = QPushButton('Add Estrutura')
        layout = QVBoxLayout(self)
        layout.addWidget(self.scroll)
        layout.addWidget(self.buttonAdd)

    #configurar botao para adicionar estruturas 
    def setButtons(self, MainClass):
        self.mainClass = MainClass
        self.buttonAdd.clicked.connect(self.addListaButton)

    #remover estruturas
    def removerButton(self, button, crop_phanton):
        self.elementos.removeWidget(button)
        self.elementos.removeWidget(crop_phanton)
        crop_phanton.hide()
        button.hide()

    #adicionar estruturas
    def addListaButton(self):
        self.updateButtons()
        num_elementos = self.elementos.rowCount()
        crop_phanton = QPushButtonLabel(self.mainClass)
        button = QPushButton()
        button.setText("Remover")
        button.clicked.connect(partial(self.removerButton, button, crop_phanton))
        size = QSize(screensize[0]/10, screensize[1]/100)
        crop_phanton.setMinimumSize(size)
        crop_phanton.setMaximumSize(size)
        crop_phanton.setFixedHeight(screensize[1]/7)
        crop_phanton.setStyleSheet('border: gray; border-style:solid; border-width: 1px;')
        crop_phanton.setText('Add new structure')
        crop_phanton.clicked.connect(partial(self.mainClass.setImage, crop_phanton))

        #chama a janela do phantom recortado
        crop_phanton.phanton = MainCrop(self.mainClass.imageDone.getImage(), 'Crop Phanton', crop_phanton)
        crop_phanton.phanton.cancelButton.clicked.connect(partial(self.removerButton, button, crop_phanton))
        self.elementos.addWidget(crop_phanton, num_elementos, 0)
        self.elementos.addWidget(button, num_elementos, 2)

# Classe principal, que chama a aplicacao
class MainClass(QWidget):
    global imgOrigin
    global imageReference

    #inicializar variaveis
    def __init__(self):
        super(QWidget, self).__init__()
        self.window = Window()
        self.window.setGeometry(200, 100, 300, 500)
        self.window.setButtons(self)
        self.imageInput = None
        self.imageOrigin = None
        self.imageDone = None
        self.imageDoneHQ = None
        self.imageCrop = None
        self.initialize = False
        self.MAX_FEATURES = 750 # Quantidade maxima de "features", de objetos a serem identificados 
        self.GOOD_MATCH_PERCENT = 0.90 # Porcentagem maxima para matches 
        self.label = QLabel() # Label para exibir a primeira imagem - phatom a ser alinhado
        self.label1 = QLabel() # Label para exibir a segunda imagem - phatom de referencia
        self.label2 = QLabel() # Label para exibir a primeira imagem alinhada 
        self.btn_aSerAlinhada = QPushButton('Carregar padrao a ser alinhado') # Phantom a ser alinhado
        self.btn_phantomReferencia = QPushButton('Carregar padrao de referencia') #Phantom referencia
        self.btn_alinhar = QPushButton('Alinhar') # Botao para executar o alinhamento
        self.btn_refazer = QPushButton('Refazer') # Botao para refazer os alinhamentos e inserir os phantoms
        self.btn_qualidade = QPushButton('Redefinir qualidade') # Botao para aplicar filtros na imagem alinhada
        self.button = QPushButton('Add Phanton') # Botao para alinhar phantoms
        self.btn_add_phantons = [] # para adicionar os phantoms em uma lista
        self.ids = 0
        self.mainCount = 0
        self.top_bar = QHBoxLayout()
        self.root = QHBoxLayout()
        self.listBox = QHBoxLayout()
        self.program = QVBoxLayout(self)
        self.scroll = QScrollArea()             # Scroll Area which contains the widgets, set as the centralWidget
        self.initUI()

    #definir itens do layout
    def initUI(self):
        #configurando as labels para exibir as imagens
        self.label.setText('Project: Image Registration - V1.0')
        self.label.setFixedWidth(screensize[0]/3-10)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet('border: gray; border-style:solid; border-width: 1px;')

        self.label1.setText('Project: Image Registration - V1.0')
        self.label1.setFixedWidth(screensize[0]/3-10)
        self.label1.setAlignment(Qt.AlignCenter)
        self.label1.setStyleSheet('border: gray; border-style:solid; border-width: 1px;')

        self.label2.setText('Project: Image Registration - V1.0')
        self.label2.setFixedWidth(screensize[0]/3-10)
        self.label2.setAlignment(Qt.AlignCenter)
        self.label2.setStyleSheet('border: gray; border-style:solid; border-width: 1px;')
        
        # chamar as funcoes ao clicar nos botoes, inserir na janela,
        # definir layout e o que deve ser habilitado ou nao
        self.btn_aSerAlinhada.clicked.connect(self.abrirImagen)
        self.top_bar.addWidget(self.btn_aSerAlinhada)
        
        self.btn_phantomReferencia.setEnabled(False)
        self.btn_phantomReferencia.clicked.connect(self.abrirOriginal)
        self.top_bar.addWidget(self.btn_phantomReferencia)

        self.btn_alinhar.setEnabled(False)
        self.btn_alinhar.clicked.connect(self.mostrarImagen)
        self.top_bar.addWidget(self.btn_alinhar)

        self.btn_refazer.setEnabled(False)
        self.btn_refazer.clicked.connect(self.refazer)
        self.top_bar.addWidget(self.btn_refazer)

        self.btn_qualidade.setEnabled(False)
        self.btn_qualidade.clicked.connect(self.qualidade)
        size = QSize(screensize[0]/11, 0)
        self.btn_qualidade.setMinimumSize(size)
        self.top_bar.addWidget(self.btn_qualidade)

        self.top_bar.setAlignment(Qt.AlignLeft)

        self.root.addWidget(self.label)
        self.root.addWidget(self.label1)
        self.root.addWidget(self.label2)

        self.button.setEnabled(False)
        size = QSize(screensize[0]/9, screensize[1]/7)
        self.button.setMinimumSize(size)

        self.listBox.addWidget(self.button)
        self.listBox.setAlignment(Qt.AlignLeft)
        self.button.clicked.connect(self.addPhantons)

        self.program.addLayout(self.top_bar)
        self.program.addLayout(self.root)
        self.program.addLayout(self.listBox)

        self.showMaximized()
        self.setWindowTitle('DICOM Files - Registration')

    #definir imagem para a estrutura recortada
    def setImage(self, thisButton):
        self.mainCount = self.mainCount + 1
        thisButton.phanton.showIt(thisButton)
        self.button.setEnabled(True)

    #funcao para remover a estrutura recortada
    def removePhantom(self, button):
        if(button.cancel):
            self.ids = self.ids - 1
            self.mainCount = self.mainCount - 1
            self.btn_add_phantons.remove(button)

        else:
            button.cancel = True
                
        #fechar a janela
        button.phanton.cancelButton.clicked.connect(button.phanton.closeIt)
        self.button.setEnabled(True)
        button.hide()
        if self.ids < 0 :
            self.ids = 0

        if self.mainCount < 0 :
            self.mainCount = 0   

    # adicionar recortes do phanton
    def addPhantons(self):
        #limite de recorte por tela
        if self.ids < 8 :
            crop_phanton = QPushButtonLabel(self)
            self.btn_add_phantons.append(crop_phanton)
            crop_phanton.setMain(self)
            crop_phanton.setText('Add new Phanton')
            size = QSize(screensize[0]/10, screensize[1]/100)
            crop_phanton.setMinimumSize(size)
            crop_phanton.setMaximumSize(size)
            crop_phanton.setFixedHeight(screensize[1]/7)
            crop_phanton.setStyleSheet('border: gray; border-style:solid; border-width: 1px;')
            crop_phanton.id = self.ids
            self.ids = self.ids + 1

            #chama a janela do phantom recortado
            crop_phanton.phanton = MainCrop(self.imageDone.getImage(), 'Crop Phanton', crop_phanton)
            crop_phanton.phanton.cancelButton.clicked.connect(partial(self.removePhantom, crop_phanton))

            self.listBox.addWidget(crop_phanton)
            self.listBox.setAlignment(Qt.AlignLeft)
            self.button.setEnabled(False)
            

        elif self.mainCount >= 8:
            self.window.show()

    #redefine o tamanho das imagens
    def processImage(self, thisImage):
        height, width = thisImage.getArray().shape
        images = thisImage.getArray()
        height = images.shape[0]
        windowScale = height* 0.002
        newX,newY = images.shape[1]/windowScale, images.shape[0]/windowScale
        images = cv2.resize(images, (int(newX), int(newY)))
        imgOrigin = cv2.convertScaleAbs(images-np.min(images), alpha=(255.0 / min(np.max(images)-np.min(images), 10000)))
        thisImage.setImage(imgOrigin)
        size = thisImage.getImage().shape
        step = thisImage.getImage().size / size[0]
        qformat = QImage.Format_Indexed8

        if len(size) == 3:
            if size[2] == 4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888

        return thisImage.getImage(), size, step, qformat

    #carrega a primeira imagem que sera alinhada
    def abrirImagen(self):
        if self.initialize == False:
            filename, _ = QFileDialog.getOpenFileName(None, 'Carregar padrao de phantom', '.', 'DICOM Files (*.dcm)')
            if filename:
                with open(filename, "rb") as file:
                    self.imageInput = DicomOrigin(pydicom.read_file(file))
                    self.imageInput.setArray(self.imageInput.getArquivo().pixel_array)
                    self.imageInput.setImageHQ(self.imageInput.getArquivo().pixel_array)

        img, size, step, qformat = self.processImage(self.imageInput)

        #cv2.imwrite('input.jpg', img)
        self.imageInput.setImage(img)

        img = QImage(self.imageInput.getImage(), size[1], size[0], step, qformat)
        img = img.rgbSwapped()

        self.label.setPixmap(QPixmap.fromImage(img))
        #self.resize(self.label.pixmap().size())
        self.btn_phantomReferencia.setEnabled(True)
        self.btn_aSerAlinhada.setEnabled(False)
        self.btn_refazer.setEnabled(True)
        self.btn_qualidade.setEnabled(False)
        # cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
        # self.imageInput = cv2.imread(filename, cv2.IMREAD_UNCHANGED)
        #self.mostrarImagen()

    #carrega a imagem original
    def abrirOriginal(self):
        if self.initialize == False:
            filename, _ = QFileDialog.getOpenFileName(None, 'Buscar Imagen', '.', 'DICOM Files (*.dcm)')
            if filename:
                with open(filename, "rb") as file:
                    self.imageOrigin = DicomNoAligned(pydicom.read_file(file))
                    self.imageOrigin.setArray(self.imageOrigin.getArquivo().pixel_array)
                    self.imageOrigin.setImageHQ(self.imageOrigin.getArquivo().pixel_array)
        
        img, size, step, qformat = self.processImage(self.imageOrigin)
        #cv2.imwrite('original.jpg', img)

        self.imageOrigin.setImage(img)

        img = QImage(self.imageOrigin.getImage(), size[1], size[0], step, qformat)
        img = img.rgbSwapped()


        self.label1.setPixmap(QPixmap.fromImage(img))
        #self.resize(self.label1.pixmap().size())

        self.btn_alinhar.setEnabled(True)
        self.btn_phantomReferencia.setEnabled(False)

    #a imagem alinhada, serve para carregar na label
    def mostrarImagen(self):
        self.imageDone = DicomAligned()
        thisImg, h = self.alignImages()
        self.imageDone.setImage(thisImg)
        size = self.imageDone.getImage().shape
        step = self.imageDone.getImage().size / size[0]
        qformat = QImage.Format_Indexed8

        if len(size) == 3:
            if size[2] == 4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888

        img = QImage(self.imageDone.getImage(), size[1], size[0], step, qformat)
        img = img.rgbSwapped()

        self.label2.setPixmap(QPixmap.fromImage(img))
        self.btn_aSerAlinhada.setEnabled(False)
        self.btn_phantomReferencia.setEnabled(False)
        self.btn_alinhar.setEnabled(False)
        self.btn_qualidade.setEnabled(True)
        self.button.setEnabled(True)
        self.initialize = True
        #self.resize(self.label2.pixmap().size())

    #para alinhar as imagens
    def alignImages(self):
        im1 = np.uint8(self.imageInput.getImage())
        im2 = np.uint8(self.imageOrigin.getImage())
        
        approache = 1
        if approache == 0:
            # identifica e destaca features de orbs
            orb = cv2.ORB_create(self.MAX_FEATURES)
            keypoints1, descriptors1 = orb.detectAndCompute(im1, None)
            keypoints2, descriptors2 = orb.detectAndCompute(im2, None)
            
            # identifica features proximos e/ou identicos
            matcher = cv2.DescriptorMatcher_create(cv2.DESCRIPTOR_MATCHER_BRUTEFORCE_HAMMING)
            matches = matcher.match(descriptors1, descriptors2, None)
            
            # organiza os matches por relevancia
            matches.sort(key=lambda x: x.distance, reverse=False)
            
            # filtra ruins matches
            numGoodMatches = int(len(matches) * self.GOOD_MATCH_PERCENT)
            matches = matches[:numGoodMatches]
            
            # gera imagens com os matches e features de ambas as imagens
            #imMatches = cv2.drawMatches(im1, keypoints1, im2, keypoints2, matches, None)
            #nameMatch = "matches" + image + ".jpg"
            #cv2.imwrite(nameMatch, imMatches)
            
            # extrai as coordenadas dos matches
            points1 = np.zeros((len(matches), 2), dtype=np.float32)
            points2 = np.zeros((len(matches), 2), dtype=np.float32)
            
            for i, match in enumerate(matches):
                points1[i, :] = keypoints1[match.queryIdx].pt
                points2[i, :] = keypoints2[match.trainIdx].pt
            
            # localiza e salva a homografia
            h, mask = cv2.findHomography(points1, points2, cv2.RANSAC)
            
            # aplica a homografia para alinhar as imagens
            height, width = im2.shape
            im1Reg = cv2.warpPerspective(im1, h, (width, height))

        elif approache == 1:
            akaze = cv2.AKAZE_create()
            kp1, des1 = akaze.detectAndCompute(im1, None)
            kp2, des2 = akaze.detectAndCompute(im2, None)

            bf = cv2.BFMatcher()
            matches = bf.knnMatch(des1, des2, k=2)
            
            good_matches = []
            for m,n in matches:
                if m.distance < 0.9*n.distance:
                    good_matches.append([m])

            ref_matched_kpts = np.float32([kp1[m[0].queryIdx].pt for m in good_matches]).reshape(-1,1,2)
            sensed_matched_kpts = np.float32([kp2[m[0].trainIdx].pt for m in good_matches]).reshape(-1,1,2)

            h, status = cv2.findHomography(ref_matched_kpts, sensed_matched_kpts, cv2.RANSAC,5.0)
            im1Reg = cv2.warpPerspective(im1, h, (im1.shape[1], im1.shape[0]))

        self.imageInput._h = h
        #cv2.imwrite('alinhada.jpg', im1Reg)
        return im1Reg, h
        
    #trata a qualidade da ultima imagem
    def qualidade(self):
        kernel = np.ones((3,3),np.float32)
        newImage = self.imageInput.getImageHQ() #retorna imagem com melhor qualidade

        # aplica erosao e dilatacao
        newImage = cv2.erode(newImage,kernel,iterations = 1)
        newImage = cv2.morphologyEx(newImage, cv2.MORPH_OPEN, kernel)

        kernel_sharpening = np.array([[-1,-1,-1], 
                                    [-1, 9,-1],
                                    [-1,-1,-1]])
        # aplica filtro de nitidez
        newImage = cv2.filter2D(newImage, -1, kernel_sharpening)
        
        # aplica filtro Gaussiano
        newImage = cv2.GaussianBlur(newImage, (3, 3), 0)

        # redimensiona a imagem e aplica o mesmo alinhamento
        height = newImage.shape[0]
        windowScale = height* 0.002
        newX,newY = newImage.shape[1]/windowScale, newImage.shape[0]/windowScale
        newImage = cv2.resize(newImage, (int(newX), int(newY)))
        imgOrigin = cv2.convertScaleAbs(newImage-np.min(newImage), alpha=(255.0 / min(np.max(newImage)-np.min(newImage), 10000)))
        height, width = imgOrigin.shape
        im1Reg = cv2.warpPerspective(imgOrigin, self.imageInput._h, (width, height))

        self.imageDone.setImage(im1Reg)
        size = self.imageDone.getImage().shape
        step = self.imageDone.getImage().size / size[0]
        qformat = QImage.Format_Indexed8

        if len(size) == 3:
            if size[2] == 4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888

        img = QImage(self.imageDone.getImage(), size[1], size[0], step, qformat)
        img = img.rgbSwapped()        

        self.label2.setPixmap(QPixmap.fromImage(img))

        # oculta os recortes ja estruturados para serem refeitos
        for i in self.btn_add_phantons:
            i.hide()

    #apaga todas as imagens
    def refazer(self):
        cleanImage = QPixmap()
        self.label.setPixmap(cleanImage)
        self.label.setText('Project: Image Registration - V1.0')

        self.label1.setPixmap(cleanImage)
        self.label1.setText('Project: Image Registration - V1.0')

        self.label2.setPixmap(cleanImage)
        self.label2.setText('Project: Image Registration - V1.0')

        self.btn_aSerAlinhada.setEnabled(True)
        self.btn_phantomReferencia.setEnabled(False)
        self.btn_alinhar.setEnabled(False)
        self.btn_refazer.setEnabled(False)
        self.button.setEnabled(False)
        self.btn_qualidade.setEnabled(False)

        for i in self.btn_add_phantons:
            i.hide()

        self.imageInput = None
        self.imageOrigin = None
        self.imageDone = None
        self.initialize = False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainClass()
    win.show()
    sys.exit(app.exec_())