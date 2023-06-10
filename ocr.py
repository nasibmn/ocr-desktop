from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.core.clipboard import Clipboard
from kivy.uix.button import Button
from fpdf import FPDF
from plyer import filechooser
from kivy.uix.widget import Widget
from kivy.core.window import Window
from matplotlib import pyplot as plt
from kivy.loader import ImageLoader
import cv2
from PIL import Image
import pytesseract
from kivy.clock import Clock
import threading

def display(im_path):
    dpi = 80
    im_data = plt.imread(im_path)

    height, width  = im_data.shape[:2]
    
    figsize = width / float(dpi), height / float(dpi)

    fig = plt.figure(figsize=figsize)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis('off')
    ax.imshow(im_data, cmap='gray')
    plt.show()


def mark_region(image_path):
    im = cv2.imread(image_path)

    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (9,9), 0)
    thresh = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,11,30)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9,9))
    dilate = cv2.dilate(thresh, kernel, iterations=4)

    cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]

    line_items_coordinates = []
    for c in cnts:
        area = cv2.contourArea(c)
        x,y,w,h = cv2.boundingRect(c)

        if y >= 600 and x <= 1000:
            if area > 10000:
                image = cv2.rectangle(im, (x,y), (2200, y+h), color=(255,0,255), thickness=3)
                line_items_coordinates.append([(x,y), (2200, y+h)])

        if y >= 2400 and x<= 2000:
            image = cv2.rectangle(im, (x,y), (2200, y+h), color=(255,0,255), thickness=3)
            line_items_coordinates.append([(x,y), (2200, y+h)])

    return image, line_items_coordinates


def grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def text_to_pdf(text, output_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=text.encode('utf-8').decode('latin-1'))
    pdf.output(output_path)


def select_output_path():
    filters = [("PDF Files", "*.pdf")]
    path = filechooser.save_file(filters=filters)

    if path:
        return path[0]

    return None


class Main(Widget):
    def __init__(self, **kwargs):
        super(Main, self).__init__(**kwargs)
        self.ids.removebtn.disabled = True
        self.image = ""
        self.clipboard = ""
        self.ids.output.halign = 'center'
        self.ids.output.padding_y = [self.height / 2]

    def select_file(self):
        threading.Thread(target=self.open_file_thread).start()

    def open_file_thread(self):
        selection = filechooser.open_file()
        if selection:
            self.image = selection[0]
            Clock.schedule_once(lambda dt: self.set_image_source(), 0)

    def set_image_source(self, *args):
        self.ids.bck.source = self.image
        self.ids.bck.texture = None
        self.ids.bck.reload()
        self.ids.convertbtn.disabled = False
        self.ids.removebtn.disabled = False


    def convert(self):
        self.ids.output.halign = 'left'
        self.ids.output.padding_y = 5
        self.ids.output.padding_x = 5
        image = cv2.imread(self.image)
        ret,thresh1 = cv2.threshold(image,120,255,cv2.THRESH_BINARY)
        text = str(pytesseract.image_to_string(thresh1, config='--psm 6'))
        self.clipboard = text
        self.ids.output.text = text[:-1]
        self.ids.clipboardbtn.disabled = False
        self.ids.pdfbtn.disabled = False
            
    def export_as_pdf(self):
        threading.Thread(target=self.export_as_pdf_thread).start()

    def export_as_pdf_thread(self):
        output_file_path = select_output_path()
        if output_file_path:
            text_to_pdf(self.clipboard, output_file_path)
            print("PDF file saved:", output_file_path)
        else:
            print("No file selected.")
            
    def copy_to_clipboard(self):
        Clipboard.copy(self.clipboard)

    def remove_file(self):
        self.ids.bck.source = 'empty.png'
        self.ids.output.text = ""
        self.ids.output.hint_text = "No Image Selected..."
        self.ids.output.halign = 'center'
        self.ids.output.padding_y = 30
        self.ids.convertbtn.disabled = True
        self.ids.removebtn.disabled = True
        self.ids.clipboardbtn.disabled = True
        self.ids.pdfbtn.disabled = True


class OCR(App):
    def build(self):
        self.title = "OPTICAL CHARACTER RECOGNITION"
        Window.size = (1100, 700)
        return Main()


if __name__ == "__main__":
    OCR().run()
