import math
import time
import tkinter
import cv2
import numpy as np
import pyautogui

APP = tkinter.Tk() #Tkinter menüsü oluşturma ve gerekli konfigürasyonlar
APP.title("Virtual Mouse") #Başlık
APP.geometry("200x150") #Boyut
APP.configure(bg='#add8e6') #Arkaplan rengi
APP.resizable(width=False, height=False) #Boyutlandırma kısıtlama

def function(boolean): #Start ya da stop tuşuna basıldığında bu fonk. çağrılır
    if boolean: #Gelen değer true ise program başlatılır
        pyautogui.FAILSAFE = False #Pyautogui güvenlik bölgesini geçersiz kılar
        screen_x, screen_y = pyautogui.size() #Ekran boyutunu alır
        click = click_message = movement_start = scroll_start = None #Gerekli tanımlamalar
        cap = cv2.VideoCapture(0) #Video yakalama başlatılır
        while cap.isOpened(): #Kamera açık olduğu süre boyunca çalışır
            _, img = cap.read() #Kameradan gelen değeri img içine atar
            camera_x, camera_y, _ = img.shape #Kamera boyutlarını alır
            img = cv2.flip(img, 1) #Gelen görüntünün dikey olarak simetriğini alır
            crop_img = img #Orijinal görüntü bozulmaması için görüntüyü yeni değişkene atar
            grey = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY) #Görüntüyü griton hale çevirir
            value = (35, 35) #Bir matris oluşturur
            blurred = cv2.GaussianBlur(grey, value, 0) #Görünütüye gauss filtresi uygulanır
            _, thresh1 = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU) #Eşik değerleri alınır
            contours, _ = cv2.findContours(thresh1.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE) #Dış hatlar bulunur
            max_area = -1 #En yüksek alanı bulmak için yeni değişken tanımlanıyor
            for i in range(len(contours)): #Dış hat sayısı kadar döngü çalışır
                cnt = contours[i] #Dış hat değeri değişkene atılır
                area = cv2.contourArea(cnt) #Alanı bulunur
                if area > max_area: #En yüksek değeri bulmak için kontrol yapılır
                    max_area = area #Değer değişkene atılır
                    c_i = i #İndex değeri de yeni değişkene atılır
            cnt = contours[c_i] #İndex değeri alınan dış hatlar değişkene atılır
            x_value, y_value, w_value, h_value = cv2.boundingRect(cnt) #Bütün değerlerin içinde bulunacağı bir dikdörtgen için gerekli dört köşe noktası alınır
            cv2.rectangle(crop_img, (x_value, y_value), (x_value + w_value, y_value + h_value),  
                          (0, 255, 0), 2) #Alınan değerlere göre dikdörtgen çizilir
            hull = cv2.convexHull(cnt) #Bütün noktaların içinde bulunacağı dış noktaların değerleri alınır
            drawing = np.zeros(crop_img.shape, np.uint8) #Alınan değerler değişkene atılır
            cv2.drawContours(drawing, [cnt], 0, (0, 255, 0), 0) #Dış hat noktaları Drawing paneline çizilir
            cv2.drawContours(drawing, [hull], 0, (0, 0, 255), 0) #Dış hat noktalarının birleşiminden oluşan çokgen Drawing paneline çizilir
            hull = cv2.convexHull(cnt, returnPoints=False) #Bütün noktaların içinde bulunacağı dış noktaların değerleri alınır
            defects = cv2.convexityDefects(cnt, hull) #Çukur(dış hat çizgisine en uzak iç nokta) değerleri alınır
            used_defect = None #Yeni değişken tanımlanır
            if defects is not None: #Herhangi bir çukur bulunduysa çalışır
                count_defects = 1 #Kaç parmak açık olduğuna ait değer
                for i in range(defects.shape[0]): #Çukur sayısı kadar çalışır
                    s_defects, e_defects, f_defects, _ = defects[i, 0] #Aşağıdaki kısım çukurların açılarını bulmayı sağlıyor
                    start = tuple(cnt[s_defects][0]) 
                    end = tuple(cnt[e_defects][0]) 
                    far = tuple(cnt[f_defects][0])
                    a_defects = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) 
                    b_defects = math.sqrt((far[0] - start[0]) ** 2 + (far[1] - start[1]) ** 2) 
                    c_defects = math.sqrt((end[0] - far[0]) ** 2 + (end[1] - far[1]) ** 2) 
                    angle = math.acos((b_defects ** 2 + c_defects ** 2 - a_defects ** 2) / 
                                      (2 * b_defects * c_defects)) * 57 
                    if angle <= 90: #Bulunan açı değeri 90 dereceden küçük olduğunda çalışır
                        count_defects += 1 #Parmak sayısına 1 ekler
                    cv2.circle(crop_img, far, 5, [255, 0, 0], -1) #Dış hat noktaları çizilir
                    cv2.line(crop_img, start, end, [255, 0, 0], 2) #Dış hat noktalarının birleşiminden oluşan çokgen çizilir
                    if count_defects == 2 and angle <= 90: #Parmak sayısı 2 ve açı 90 dereceden küçük ise çalışır
                        used_defect = {"x": start[0], "y": start[1]} #X ve y değerleri alınır 
                    if count_defects >= 5: #5'ten fazla parmak bulması durumunda çalışır 
                        count_defects = 5 #Hata olmaması için en fazla parmak sayısı 5'e sabitlenir
            if used_defect is not None: #Alınan herhangi bir konum varsa çalışır
                best = used_defect #Yeni değişkene atılır
                if count_defects == 2: #2 parmak olması durumunda çalışır
                    x_movement = best['x'] #X değeri yeni değişkene atılır
                    y_movement = best['y'] #Y değeri yeni değişkene atılır
                    display_x = x_movement #X değeri yeni değişkene atılır
                    display_y = y_movement #Y değeri yeni değişkene atılır
                    if movement_start is not None: #Yer değiştirme olduysa çalışır
                        m_start = (x_movement, y_movement) #Başlangıç x ve y değerleri alınır
                        x_movement = x_movement - movement_start[0] #X ekseninde hareketin hangi yönde ne kadar olduğunu belirler
                        y_movement = y_movement - movement_start[1] #Y ekseninde hareketin hangi yönde ne kadar olduğunu belirler
                        x_movement = x_movement * (screen_x / camera_x) #Ekran/Kamera oranı ile x ekseninde hareket çarpılır
                        y_movement = y_movement * (screen_y / camera_y) #Ekran/Kamera oranı ile y ekseninde hareket çarpılır
                        movement_start = m_start #yeni değişene atılır
                        print("X: " + str(x_movement) + " Y: " + str(y_movement)) #Anlık komutu çıktı olarak yazar
                        pyautogui.moveRel(x_movement, y_movement) #Mouse hareket işlemini yapar 
                    else:
                        movement_start = (x_movement, y_movement) #X ve y değerleri değişkene atılır
                    cv2.circle(crop_img, (display_x, display_y), 5, [255, 255, 255], 20) #Asıl olarak takip edilen konuma işaret koyar
                elif count_defects == 3: #Parmak sayısı 3 olduğunda çalışır
                    click_message = "SCROLLING" #Mesajın içeriği yazılır
                    x_scroll = best['x'] #X değeri yeni değişkene atılır
                    y_scroll = best['y'] #Y değeri yeni değişkene atılır
                    display_x = x_scroll #X değeri yeni değişkene atılır
                    display_y = y_scroll #Y değeri yeni değişkene atılır
                    if scroll_start is not None: #Başlangıç değerleri atıldıysa çalışır
                        x_scroll = x_scroll - scroll_start[0] #X ekseninde hareketin hangi yönde ne kadar olduğunu belirler
                        y_scroll = y_scroll - scroll_start[1] #Y ekseninde hareketin hangi yönde ne kadar olduğunu belirler
                        x_scroll = x_scroll * (screen_x / camera_x) #Ekran/Kamera oranı ile x ekseninde hareket çarpılır
                        y_scroll = y_scroll * (screen_y / camera_y) #Ekran/Kamera oranı ile y ekseninde hareket çarpılır
                        if y_scroll > 0: #Y ekseninde hareket aşağı doğruysa çalışır
                            pyautogui.scroll(-50, x_scroll, y_scroll) #Yukarı doğru kaydırma gerçekleştirilir
                        elif y_scroll < 0: #Y ekseninde hareket yukarı doğruysa çalışır
                            pyautogui.scroll(50, x_scroll, y_scroll) #Aşağı doğru kaydırma gerçekleştirilir
                    else:
                        scroll_start = (x_scroll, y_scroll) #Gerekli başlangıç değerleri verilir
                    cv2.circle(crop_img, (display_x, display_y), 5, [255, 255, 255], 20) #Asıl olarak takip edilen konuma işaret koyar
                elif count_defects == 4 and click is None: #Parmak sayısı 4 ve tıklama işlemi yapılmıyorsa çalışır
                    click = time.time() #Alınan zaman değişkene atılır
                    click_message = "LEFT CLICK" #Mesajın içeriği yazılır
                    pyautogui.click() #Sol tıklama işlemi yapılır
                    pyautogui.sleep(0.5) #İşlemden sonra kısa bir bekleme süresi eklenir
                elif count_defects == 5 and click is None: #Parmak sayısı 5 ve tıklama işlemi yapılmıyorsa çalışır
                    click = time.time() #Alınan zaman değişkene atılır
                    click_message = "RIGHT CLICK" #Mesajın içeriği yazılır
                    pyautogui.rightClick() #Sağ tıklama işlemi yapılır
                    pyautogui.sleep(0.5) #İşlemden sonra kısa bir bekleme süresi eklenir   
            else:
                movement_start = scroll_start = None #Eski değerler silinir
            if click is not None: #Tıklama olayı olduysa çalışır
                cv2.putText(img, click_message, (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 3, 3) #Ekrana mesajı yazar
                if click < time.time(): #Tıklama olayından bir süre sonra çalışır
                    click = None #Eski değer silinir
            cv2.putText(img, "Defects: " + str(count_defects), (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, 2) #Parmak sayısını ekrana yazar
            cv2.imshow('Virtual Mouse', img) #Kamera görüntüsünü ekranda gösterir
            cv2.imshow('Drawing', drawing) #Çizim görüntüsünü ekranda gösterir
            k = cv2.waitKey(10) #Klavyeden girdi almayı sağlar
            if k == 27: #Escape tuşunu basılınca çalışır
                break #Programın sonlanmasını sağlar
    try: #Programın bozulup kapanmasını engeller
        cap.release() #Görüntü yakalamayı sonlandırır
    except:
        print("No error") #İşlemde hata olmadıysa çalışır
    cv2.destroyAllWindows() #Pencereleri kapatır
def stop_virtual_mouse(): #Stop butonuna basıldığında çalışır
    STOP_BUTTON.configure(state=tkinter.DISABLED) #Stop butonunu pasif hale getirir
    START_BUTTON.configure(state=tkinter.NORMAL) #Start butonunu aktif hale getirir
    function(False) #Programı sonlandırır
def start_virtual_mouse(): #Start butonuna basıldığında çalışır
    START_BUTTON.configure(state=tkinter.DISABLED) #Start butonunu pasif hale getirir
    STOP_BUTTON.configure(state=tkinter.NORMAL) #Stop butonunu aktif hale getirir
    function(True) #Programı başlatır
START_BUTTON = tkinter.Button(APP, text="Start", command=start_virtual_mouse, bg='black',
                              fg='white', width=4, height=5, relief="groove",
                              font=("MS Serif", 30, "bold")) #Butonun özellikleri
STOP_BUTTON = tkinter.Button(APP, text="Stop", command=stop_virtual_mouse, state=tkinter.DISABLED,
                             bg='black', fg='white', width=4, height=5, relief="groove",
                             font=("MS Serif", 30, "bold")) #Butonun özellikleri
START_BUTTON.pack(side=tkinter.LEFT) #Butonu sol tarafta tutar
STOP_BUTTON.pack(side=tkinter.RIGHT) #Butonu sağ tarafta tutar
APP.mainloop() #Tkinter menüsünü çalıştırır
