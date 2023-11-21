import cv2
import numpy as np
from time import sleep

class SubtrairFundo:
    def __init__(self):
        self.subtracao = cv2.createBackgroundSubtractorMOG2(history=60, detectShadows=False, varThreshold=100)

    def aplicar_subtracao(self, roi_blur):
        return self.subtracao.apply(roi_blur)

class SelecionarRegiaoInteresse:
    def __init__(self, frame):
        self.bbox = cv2.selectROI(frame, False)
        (self.w1, self.h1, self.w2, self.h2) = self.bbox

    def selecionar_area(self, frame):
        return frame[self.h1:self.h1 + self.h2, self.w1:self.w1 + self.w2]

    def desenhar_linhas(self, frame):
        centro_x = self.w1 + self.w2 // 2
        centro_y = self.h1 + self.h2 // 2
        cv2.line(frame, (self.w1, centro_y), (self.w1 + self.w2, centro_y), (255, 255, 255), 2)
        

class ContadorVeiculos:
    def __init__(self, pos_linha, offset):
        self.pos_linha = pos_linha
        self.offset = offset
        self.carros = 0
        self.texto_contagem = "Carros detectados: 0"
        self.posicoes_anteriores = set()

    def contar_veiculos(self, detec):
        for(x, y) in detec:
            if (self.pos_linha + self.offset) > y > (self.pos_linha - self.offset):
                self.carros += 1
                detec.remove((x, y))
                self.texto_contagem = "Carros detectados:" + str(self.carros)

class DetectarVeiculo:
    def __init__(self, w1, h1, w2, contador_veiculos):
        self.w1 = w1
        self.h1 = h1
        self.w2 = w2
        self.contador_veiculos = contador_veiculos
        self.detec = []

    def detectar_veiculo(self, frame, dilatado):
        contours, _ = cv2.findContours(dilatado, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for (i, c) in enumerate(contours):
            (x, y, w, h) = cv2.boundingRect(c)
            validar_contorno = (w >= 100) and (h >= 100)
            if not validar_contorno:
                continue
            cv2.rectangle(frame, (x + self.w1, y + self.h1), (x + self.w1 + w, y + self.h1 + h), (0, 255, 0), 2)
            centro_x = x + self.w1 + w // 2
            centro_y = y + self.h1 + h // 2
            centro = centro_x, centro_y
            self.detec.append(centro)
            cv2.circle(frame, (centro_x, centro_y), 2, (0, 255, 255), -1)
            self.contador_veiculos.contar_veiculos(self.detec)

        
        cv2.putText(frame, self.contador_veiculos.texto_contagem, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
class Video:
    def __init__(self, caminho_video):
        self.captura = cv2.VideoCapture(caminho_video)
        _, self.frame = self.captura.read()

        self.subtracao_fundo = SubtrairFundo()
        self.selecao_roi = SelecionarRegiaoInteresse(self.frame)
        self.contador_veiculos = ContadorVeiculos(self.selecao_roi.h1 + self.selecao_roi.h2 // 2, 10)
        self.deteccao_veiculo = DetectarVeiculo(self.selecao_roi.w1, self.selecao_roi.h1, self.selecao_roi.w2, self.contador_veiculos)

    def processar_video(self):
        while True:
            ret, self.frame = self.captura.read()
            tempo = float(1/60)
            sleep(tempo)
            if self.frame is None:
                break

            roi = self.selecao_roi.selecionar_area(self.frame)
            roi_tons_cinza = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            roi_blur = cv2.GaussianBlur(roi_tons_cinza, (5,5), 5)

            subtraido = self.subtracao_fundo.aplicar_subtracao(roi_blur)
            
            dilatado = self.aplicar_filtros(subtraido)

            self.selecao_roi.desenhar_linhas(self.frame)

            self.deteccao_veiculo.detectar_veiculo(self.frame, dilatado)

            cv2.imshow('Video c/ filtros', dilatado)
            cv2.imshow("ROI", roi)
            cv2.imshow("Frame", self.frame)

            if cv2.waitKey(1) == ord('q'):  # Pressionar q para fechar
                break

        self.captura.release()
        cv2.destroyAllWindows()

    def aplicar_filtros(self, subtraido):
        closing = cv2.morphologyEx(subtraido, cv2.MORPH_CLOSE, np.ones((10, 10), np.uint8), iterations=3)
        opening = cv2.morphologyEx(closing, cv2.MORPH_OPEN, np.ones((10, 10), np.uint8), iterations=3)
        dilated = cv2.dilate(opening, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8)), iterations=3)
        return dilated

video = Video("videos/traffic.mp4")
video.processar_video()