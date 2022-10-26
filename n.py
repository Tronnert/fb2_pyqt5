import sqlite3
import sys
import os.path
import shutil

from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QFileDialog, QInputDialog
from PyQt5.QtWidgets import QMainWindow, QWidget, QFontDialog
from PyQt5.QtGui import QPixmap
from bs4 import BeautifulSoup  # lxml также нужен
import io
import base64
from PIL import Image, ImageQt


class BookForTable(QWidget):
    def __init__(self, book, *args):
        super().__init__(*args)
        uic.loadUi('book_1.ui', self)
        im = Image.open(book.abs_path_to_cover).resize((157, 189))
        self.im1 = ImageQt.ImageQt(im)
        self.pix_im = QPixmap.fromImage(self.im1)
        self.q_image.setPixmap(self.pix_im)
        self.q_title.setText(book.title)
        self.q_genres.setText(book.genres)
        self.q_author.setText(book.author)
        self.book = book
        # self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))


class BookAct(QWidget):
    def __init__(self, book, *args):
        super().__init__(*args)
        uic.loadUi('book_2.ui', self)
        self.im1 = ImageQt.ImageQt(Image.open(
            book.abs_path_to_cover).resize((211, 271)))
        self.pix_im = QPixmap.fromImage(self.im1)
        self.q_image.setPixmap(self.pix_im)
        self.q_title.setText(book.title)
        self.q_author.setText(book.author)
        self.move(10, 0)
        self.hide()


class Book:
    def __init__(self, data, *parents):
        self.abs_path_to_book, self.title, self.author, self.genres, self.abs_path_to_cover, self.codec = data

        self.book_for_table = BookForTable(self)
        self.book_act = BookAct(self, parents[1])

        self.reader = Reader(self, parents[1])

    def copy(self):
        return BookForTable(self)


class Reader(QMainWindow):
    def __init__(self, book, main):
        super().__init__()
        uic.loadUi('reader.ui', self)
        self.libs_btn.clicked.connect(self.go_to_main_page)
        self.main = main
        self.book = book
        f = open(
            self.main.path + "/" +
            self.book.abs_path_to_book[:-4].replace("/", "") + "/" + "text.txt",
            encoding=self.book.codec)
        self.textEdit.setHtml(f.read())
        f.close()
        f = open(
            self.main.path + "/" +
            self.book.abs_path_to_book[:-4].replace("/", "") + "/" + "text.txt",
            encoding=self.book.codec, mode="w")
        f.write(self.textEdit.toHtml())
        f.close()

        self.label.setText(self.book.title)
        self.settings_btn.clicked.connect(self.change_font)

    def go_to_main_page(self):
        self.main.move(self.x(), self.y())
        self.main.show()
        self.hide()

    def change_font(self):
        font, ok = QFontDialog.getFont()
        if ok:
            self.textEdit.setFont(font)


class Main(QMainWindow):
    def __init__(self):
        super().__init__()

        self.path = os.getcwd()
        # print(self.path)
        if not os.path.exists("test.db"):
            self.sqlconnect = sqlite3.connect('test.db')
            self.sqlconnect.cursor().execute("""CREATE TABLE books (
    id        INTEGER UNIQUE
                      NOT NULL
                      PRIMARY KEY AUTOINCREMENT,
    path      STRING  UNIQUE
                      NOT NULL,
    title     STRING,
    author    STRING,
    genres    STRING,
    cover     STRING  UNIQUE
                      NOT NULL,
    codec     STRING  NOT NULL,
    read_date INTEGER NOT NULL
);""")
            self.sqlconnect.cursor().execute("""
CREATE TABLE genres (
    id    INTEGER PRIMARY KEY AUTOINCREMENT
                  UNIQUE
                  NOT NULL,
    title STRING  UNIQUE
                  NOT NULL
);""")
            self.sqlconnect.commit()
        else:
            self.sqlconnect = sqlite3.connect('test.db')

        uic.loadUi('main.ui', self)

        self.load.clicked.connect(self.add_to_books)
        self.read.clicked.connect(self.go_to_reader_page)

        self.table.setRowCount(0)
        self.table.setColumnCount(1)
        self.books = []
        self.table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.table.horizontalHeader().resizeSection(0, 467)
        self.table.setCurrentCell(0, 0)

        self.open_sql()

        self.sortings = ["Сортировать по названию", "Сортировать по дате прочтения",
                         "Сортировать по дате добавления"]
        self.sortings_btn = [self.sort_title, self.sort_read, self.sort_add]
        self.sortings_fonts = [8, 7, 7]

        self.finding = ["Поиск по названию",
                        "Поиск по автору", "Поиск по жанрам"]
        self.finding_btn = [self.find_title,
                            self.find_author, self.find_genres]

        self.sort_title.clicked.connect(self.book_sort_title)
        self.sort_add.clicked.connect(self.book_sort_id)
        self.sort_read.clicked.connect(self.book_sort_read_date)

        self.find_title.clicked.connect(self.find_by_title)
        self.find_author.clicked.connect(self.find_by_author)
        self.find_genres.clicked.connect(self.find_by_genres)

        self.table.currentCellChanged.connect(self.p)

    def go_to_reader_page(self):
        read_date = str(int(self.sqlconnect.cursor().execute("""SELECT MAX(read_date) 
                    FROM books""").fetchone()[0]) + 1)
        self.sqlconnect.cursor().execute("""UPDATE books
SET read_date = ?
WHERE path = ?""", (read_date, self.old.book.abs_path_to_book))
        self.sqlconnect.commit()
        self.old.book.reader.move(self.x(), self.y())
        self.old.book.reader.show()
        self.hide()

    def open_sql(self):
        for e in self.sqlconnect.cursor().execute("""SELECT * FROM books"""):
            self.books.append(Book(e[1:-1], self.table, self))
            self.table.setRowCount(self.table.rowCount() + 1)
            self.table.setCellWidget(
                self.table.rowCount() - 1, 0, self.books[-1].book_for_table)
            self.table.verticalHeader().resizeSection(self.table.rowCount() - 1, 196)
        if self.books:
            self.books[0].book_act.show()
            self.old = self.table.cellWidget(0, 0)
        else:
            self.old = False

    def p(self):
        if self.old:
            self.old.book.book_act.hide()
        self.old = self.table.cellWidget(self.table.currentRow(), 0)
        try:
            self.old.book.book_act.show()
        except:
            pass

    def add_to_books(self):
        fname = QFileDialog.getOpenFileName(
            self, 'Выбрать книгу', '', 'Картинка (*.fb2)')[0]
        if fname:
            if fname in map(lambda x: x[0], self.sqlconnect.cursor().execute("""SELECT path FROM books""").fetchall()):
                self.sqlconnect.cursor().execute("""DELETE FROM books WHERE path = ?""", (fname,))
                self.sqlconnect.commit()
                shutil.rmtree(self.path + "/" +
                              fname[:-4].replace("/", ""))
                for e in range(len(self.books)):
                    if self.books[e].abs_path_to_book == fname:
                        self.books = self.books[:e] + self.books[e + 1:]
                        self.table.removeRow(e)
                        break

            self.books.append(Book(self.add_to_sql(fname), self.table, self))
            self.table.setRowCount(self.table.rowCount() + 1)
            self.table.setCellWidget(
                self.table.rowCount() - 1, 0, self.books[-1].book_for_table)
            self.table.verticalHeader().resizeSection(self.table.rowCount() - 1, 196)
            self.table.setCurrentCell(self.table.rowCount() - 1, 0)
            self.p()
            # print(self.books)

    def add_to_sql(self, abs_path):
        b = None
        codec = ""
        for e in ["windows-1251", "UTF-8"]:
            try:
                file = open(abs_path, encoding=e)
                b = file.read()
                codec = e
                file.close()
                break
            except UnicodeError:
                pass
        if b is None:
            raise UnicodeError

        book = BeautifulSoup(b, "lxml")
        book_file_name = abs_path.split("/")[-1]
        title = self.return_book_title(book)
        author = " ".join(self.return_author(book))
        genres_ordinary = self.return_genres(book)
        im = book.description.select(
            "title-info coverpage image")[0]["l:href"][1:]

        # print(self.path + "/" + self.book_name[:-4])
        os.mkdir(self.path + "/" +
                 abs_path[:-4].replace("/", ""))

        self.macking_images(book, abs_path)
        abs_path_to_cover = self.path + "/" + \
            abs_path[:-4].replace("/", "") + "/" + im

        read_date = 0

        self.sqlconnect.cursor().execute("""INSERT INTO books(path, title, author, genres, cover, codec, read_date) 
        VALUES""" + (
            abs_path, title, author, ", ".join(genres_ordinary), abs_path_to_cover, codec, read_date).__str__())
        self.sqlconnect.commit()

        genres_existed = self.sqlconnect.cursor().execute(
            """SELECT title FROM genres""").fetchall()
        genres_set = list(set(genres_ordinary) -
                          set(list(map(lambda x: x[0], genres_existed))))
        for e in genres_set:
            self.sqlconnect.cursor().execute(
                """INSERT INTO genres(title) VALUES(?)""", (e,))
            self.sqlconnect.commit()

        file_to_write = open(self.path + "/" + abs_path[:-4].replace("/", "") + "/" + "text.txt",
                             mode="w", encoding=codec)
        for s in book.select("strong"):
            s.name = "b"
        for s in book.select("emphasis"):
            s.name = "i"
        for v in book.select("v"):
            v.name = "p"
        for s in book.select("image"):
            src = self.path + "/" + \
                abs_path[:-4].replace("/", "") + \
                "/" + s["l:href"][1:]
            del s["l:href"]
            s["src"] = src
            s.name = "img"
        for e in book.select("empty-line"):
            e.name = "br"
        for e in range(len(book.select("binary"))):
            book.binary.decompose()
        book.description.decompose()
        book.fictionbook.title.name = "h1"
        for e in range(len(book.select("title"))):
            book.title.name = "h2"
        file_to_write.write(book.prettify().__str__())
        file_to_write.close()

        return abs_path, title, author, ", ".join(genres_ordinary), abs_path_to_cover, codec

    def macking_images(self, soup, abs_name):
        binar = soup.select("binary")
        for futere_img in binar:
            img = Image.open(io.BytesIO(
                base64.decodebytes(bytes(futere_img.text, "utf-8"))))
            w, h = img.size
            if w < 702 or h < 622:
                if w >= h:
                    img = img.resize((692, int(692 * h / w)))
                else:
                    img = img.resize((int(595 * w / h), 595))
            abs_path_to_cover = self.path + "/" + abs_name[:-4].replace("/", "") + "/" + futere_img[
                "id"]
            print(abs_path_to_cover)
            img.save(abs_path_to_cover)

    def find_by_genres(self):
        if "Отменить" not in self.finding_btn[2].text():
            genres = list(map(lambda x: x[0], self.sqlconnect.cursor().execute("""SELECT title 
            FROM genres""").fetchall()))
            author, ok_pressed = QInputDialog.getItem(
                self, "Выберите жанр", "Выберите жанр", genres, 0, False)
            if ok_pressed:
                sorted_id = self.sqlconnect.cursor().execute("""SELECT id FROM books 
                WHERE genres LIKE '%""" + author + """%'""").fetchall()
                self.table.clear()
                self.table.setRowCount(0)
                for j in sorted_id:
                    self.table.setRowCount(self.table.rowCount() + 1)
                    widgt = self.books[int(j[0]) - 1].copy()
                    self.table.setCellWidget(
                        self.table.rowCount() - 1, 0, widgt)
                    self.table.verticalHeader().resizeSection(self.table.rowCount() - 1, 196)

                self.sortings_btn[1].setText(self.sortings[1])
                font = self.sortings_btn[1].font()
                font.setPointSize(self.sortings_fonts[1])
                self.sortings_btn[1].setFont(font)

                self.sortings_btn[2].setText(self.sortings[2])
                font = self.sortings_btn[2].font()
                font.setPointSize(self.sortings_fonts[2])
                self.sortings_btn[2].setFont(font)
                self.sortings_btn[0].setText(self.sortings[0])
                font = self.sortings_btn[0].font()
                font.setPointSize(self.sortings_fonts[0])
                self.sortings_btn[0].setFont(font)

                self.finding_btn[2].setText("Отменить поиск")
                self.finding_btn[0].setText(self.finding[1])
                self.finding_btn[1].setText(self.finding[2])

                self.table.setCurrentCell(0, 0)
                self.p()
        else:
            self.table.clear()
            self.table.setRowCount(0)
            for e, j in enumerate(self.books):
                self.table.setRowCount(self.table.rowCount() + 1)
                self.table.setCellWidget(
                    self.table.rowCount() - 1, 0, j.copy())
                self.table.verticalHeader().resizeSection(self.table.rowCount() - 1, 196)
            self.finding_btn[2].setText(self.finding[0])
            self.table.setCurrentCell(0, 0)
            self.p()

    def find_by_author(self):
        if "Отменить" not in self.finding_btn[1].text():
            author, ok_pressed = QInputDialog.getText(self, "Введите автора",
                                                      "Введите автора")
            if ok_pressed:
                sorted_id = self.sqlconnect.cursor().execute("""SELECT id FROM books 
                WHERE author LIKE '%""" + author + """%'""").fetchall()
                self.table.clear()
                self.table.setRowCount(0)
                for j in sorted_id:
                    self.table.setRowCount(self.table.rowCount() + 1)
                    widgt = self.books[int(j[0]) - 1].copy()
                    self.table.setCellWidget(
                        self.table.rowCount() - 1, 0, widgt)
                    self.table.verticalHeader().resizeSection(self.table.rowCount() - 1, 196)

                self.sortings_btn[1].setText(self.sortings[1])
                font = self.sortings_btn[1].font()
                font.setPointSize(self.sortings_fonts[1])
                self.sortings_btn[1].setFont(font)

                self.sortings_btn[2].setText(self.sortings[2])
                font = self.sortings_btn[2].font()
                font.setPointSize(self.sortings_fonts[2])
                self.sortings_btn[2].setFont(font)
                self.sortings_btn[0].setText(self.sortings[0])
                font = self.sortings_btn[0].font()
                font.setPointSize(self.sortings_fonts[0])
                self.sortings_btn[0].setFont(font)

                self.finding_btn[1].setText("Отменить поиск")
                self.finding_btn[0].setText(self.finding[1])
                self.finding_btn[2].setText(self.finding[2])

                self.table.setCurrentCell(0, 0)
                self.p()
        else:
            self.table.clear()
            self.table.setRowCount(0)
            for e, j in enumerate(self.books):
                self.table.setRowCount(self.table.rowCount() + 1)
                self.table.setCellWidget(
                    self.table.rowCount() - 1, 0, j.copy())
                self.table.verticalHeader().resizeSection(self.table.rowCount() - 1, 196)
            self.finding_btn[1].setText(self.finding[0])
            self.table.setCurrentCell(0, 0)
            self.p()

    def find_by_title(self):
        if "Отменить" not in self.finding_btn[0].text():
            title, ok_pressed = QInputDialog.getText(self, "Введите название",
                                                     "Введите название")
            if ok_pressed:
                sorted_id = self.sqlconnect.cursor().execute("""SELECT id FROM books 
                WHERE title LIKE '%""" + title + """%'""").fetchall()
                self.table.clear()
                self.table.setRowCount(0)
                for j in sorted_id:
                    self.table.setRowCount(self.table.rowCount() + 1)
                    widgt = self.books[int(j[0]) - 1].copy()
                    print(widgt)
                    self.table.setCellWidget(
                        self.table.rowCount() - 1, 0, widgt)
                    self.table.verticalHeader().resizeSection(self.table.rowCount() - 1, 196)

                self.sortings_btn[1].setText(self.sortings[1])
                font = self.sortings_btn[1].font()
                font.setPointSize(self.sortings_fonts[1])
                self.sortings_btn[1].setFont(font)

                self.sortings_btn[2].setText(self.sortings[2])
                font = self.sortings_btn[2].font()
                font.setPointSize(self.sortings_fonts[2])
                self.sortings_btn[2].setFont(font)
                self.sortings_btn[0].setText(self.sortings[0])
                font = self.sortings_btn[0].font()
                font.setPointSize(self.sortings_fonts[0])
                self.sortings_btn[0].setFont(font)

                self.finding_btn[0].setText("Отменить поиск")
                self.finding_btn[1].setText(self.finding[1])
                self.finding_btn[2].setText(self.finding[2])

                self.table.setCurrentCell(0, 0)
                self.p()
        else:
            self.table.clear()
            self.table.setRowCount(0)
            for e, j in enumerate(self.books):
                self.table.setRowCount(self.table.rowCount() + 1)
                self.table.setCellWidget(
                    self.table.rowCount() - 1, 0, j.copy())
                self.table.verticalHeader().resizeSection(self.table.rowCount() - 1, 196)
            self.finding_btn[0].setText(self.finding[0])
            self.table.setCurrentCell(0, 0)
            self.p()

    def book_sort_title(self):
        if "Отменить" not in self.sortings_btn[0].text():
            sorted_id = self.sqlconnect.cursor().execute(
                """SELECT id FROM books ORDER BY title""").fetchall()
            self.table.clear()
            self.table.setRowCount(0)
            for j in sorted_id:
                self.table.setRowCount(self.table.rowCount() + 1)
                widgt = self.books[int(j[0]) - 1].copy()
                self.table.setCellWidget(self.table.rowCount() - 1, 0, widgt)
                self.table.verticalHeader().resizeSection(self.table.rowCount() - 1, 196)
            self.sender().setText("Отменить сортировку")
            font = self.sender().font()
            font.setPointSize(8)
            self.sender().setFont(font)

            self.sortings_btn[1].setText(self.sortings[1])
            font = self.sortings_btn[1].font()
            font.setPointSize(self.sortings_fonts[1])
            self.sortings_btn[1].setFont(font)

            self.sortings_btn[2].setText(self.sortings[2])
            font = self.sortings_btn[2].font()
            font.setPointSize(self.sortings_fonts[2])
            self.sortings_btn[2].setFont(font)

            self.table.setCurrentCell(0, 0)
            self.p()
        else:
            self.table.clear()
            for e, j in enumerate(self.books):
                self.table.setCellWidget(e, 0, j.copy())
            self.sender().setText(self.sortings[0])
            font = self.sender().font()
            font.setPointSize(self.sortings_fonts[0])
            self.sender().setFont(font)
            self.table.setCurrentCell(0, 0)
            self.p()

    def book_sort_id(self):
        if "Отменить" not in self.sortings_btn[2].text():
            sorted_id = self.sqlconnect.cursor().execute(
                """SELECT id FROM books ORDER BY id""").fetchall()
            self.table.clear()
            self.table.setRowCount(0)
            for j in sorted_id:
                self.table.setRowCount(self.table.rowCount() + 1)
                widgt = self.books[int(j[0]) - 1].copy()
                self.table.setCellWidget(self.table.rowCount() - 1, 0, widgt)
                self.table.verticalHeader().resizeSection(self.table.rowCount() - 1, 196)
            self.sender().setText("Отменить сортировку")
            font = self.sender().font()
            font.setPointSize(8)
            self.sender().setFont(font)

            self.sortings_btn[0].setText(self.sortings[0])
            font = self.sortings_btn[0].font()
            font.setPointSize(self.sortings_fonts[0])
            self.sortings_btn[0].setFont(font)

            self.sortings_btn[1].setText(self.sortings[1])
            font = self.sortings_btn[1].font()
            font.setPointSize(self.sortings_fonts[1])
            self.sortings_btn[1].setFont(font)

            self.table.setCurrentCell(0, 0)
            self.p()
        else:
            self.table.clear()
            for e, j in enumerate(self.books):
                self.table.setCellWidget(e, 0, j.copy())
            self.sender().setText(self.sortings[2])
            font = self.sender().font()
            font.setPointSize(self.sortings_fonts[2])
            self.sender().setFont(font)

            self.table.setCurrentCell(0, 0)
            self.p()

    def book_sort_read_date(self):
        print(9)
        if "Отменить" not in self.sortings_btn[1].text():
            sorted_id = list(reversed(self.sqlconnect.cursor().execute("""SELECT id FROM books 
            ORDER BY read_date""").fetchall()))
            self.table.clear()
            self.table.setRowCount(0)
            print(list(sorted_id))
            for j in sorted_id:
                self.table.setRowCount(self.table.rowCount() + 1)
                widgt = self.books[int(j[0]) - 1].copy()
                print(widgt)
                self.table.setCellWidget(self.table.rowCount() - 1, 0, widgt)
                self.table.verticalHeader().resizeSection(self.table.rowCount() - 1, 196)
            self.sender().setText("Отменить сортировку")
            font = self.sender().font()
            font.setPointSize(8)
            self.sender().setFont(font)

            self.sortings_btn[2].setText(self.sortings[2])
            font = self.sortings_btn[2].font()
            font.setPointSize(self.sortings_fonts[2])
            self.sortings_btn[2].setFont(font)

            self.sortings_btn[0].setText(self.sortings[0])
            font = self.sortings_btn[0].font()
            font.setPointSize(self.sortings_fonts[0])
            self.sortings_btn[0].setFont(font)
        else:
            # self.table.clear()
            for e, j in enumerate(self.books):
                self.table.setCellWidget(e, 0, j.copy())
            self.sender().setText(self.sortings[1])
            font = self.sender().font()
            font.setPointSize(self.sortings_fonts[1])
            self.sender().setFont(font)

    def return_genres(self, book):
        return [e.text for e in book.description.select("title-info genre")]

    def return_author(self, book):
        a = []
        for e in ["first-name", "middle-name", "last-name"]:
            b = book.description.select("title-info author " + e)
            if b:
                a.append(b[0].text)
        return a

    def return_book_title(self, book):
        return book.description.select("title-info book-title")[0].text


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Main()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
