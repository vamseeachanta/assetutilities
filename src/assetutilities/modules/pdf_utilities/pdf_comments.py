from typing import Dict, List
import sys
import urllib
import os

import fitz

# from pprint import pprint
# import poppler
from pdfannots import process_file

# https://stackoverflow.com/questions/1106098/parse-annotations-from-a-pdf


class PDFComments:

    def __init__(self):
        pass

    def method_1(self, pdf_filename):

        document = poppler.document_new_from_file(pdf_filename, None)
        n_pages = document.get_n_pages()
        all_annots = 0

        for i in range(n_pages):
            page = document.get_page(i)
            annot_mappings = page.get_annot_mapping()
            num_annots = len(annot_mappings)
            if num_annots > 0:
                for annot_mapping in annot_mappings:
                    if (
                        annot_mapping.annot.get_annot_type().value_name
                        != "POPPLER_ANNOT_LINK"
                    ):
                        all_annots += 1
                        print(
                            "page: {0:3}, {1:10}, type: {2:10}, content: {3}".format(
                                i + 1,
                                annot_mapping.annot.get_modified(),
                                annot_mapping.annot.get_annot_type().value_nick,
                                annot_mapping.annot.get_contents(),
                            )
                        )

        if all_annots > 0:
            print(str(all_annots) + " annotation(s) found")
        else:
            print("no annotations found")

    def get_pdf_annots(self, pdf_filename) -> Dict[int, List[str]]:
        """
        Return example:
        {
            0: ["Human3.6M", "Our method"],
            3: [
                "pretrained using 3D mocap data"
            ],
        }
        """
        annots_dict = dict()
        document = process_file(open(pdf_filename, "rb"))
        for page_idx in range(len(document.pages)):
            annots = document.pages[page_idx].annots
            for annot in annots:
                if page_idx not in annots_dict:
                    annots_dict[page_idx] = []

                text = "".join(annot.text).strip()
                text = text.replace("-\n", "").replace("\n", " ")
                annots_dict[page_idx].append(text)
        return annots_dict

    def _parse_highlight(self, annot: fitz.Annot, wordlist: list) -> str:
        points = annot.vertices
        quad_count = int(len(points) / 4)
        sentences = ["" for i in range(quad_count)]
        for i in range(quad_count):
            r = fitz.Quad(points[i * 4 : i * 4 + 4]).rect
            words = [w for w in wordlist if fitz.Rect(w[:4]).intersects(r)]
            sentences[i] = " ".join(w[4] for w in words)
        sentence = " ".join(sentences)
        return sentence

    def use_fitz(self, pdf_filename) -> dict:
        doc = fitz.open(pdf_filename)
        page = doc[0]

        wordlist = page.getText("words")  # list of words on page
        wordlist.sort(key=lambda w: (w[3], w[0]))  # ascending y, then x

        highlights = {}
        annot = page.firstAnnot
        i = 0
        while annot:
            if annot.type[0] == 8:
                highlights[i] = self._parse_highlight(annot, wordlist)
                i += 1
                print("> " + highlights[i] + "\n")
            annot = annot.next

        # pprint(highlights)
        return highlights


if __name__ == "__main__":
    pdf_comments = PDFComments()
    # pdf_comments.get_pdf_annots(
    #     pdf_filename=
    #     'C:/Users/ss7a2365/Desktop/Comments.pdf'
    # )
    pdf_comments.use_fitz(pdf_filename="C:/Users/ss7a2365/Desktop/Comments.pdf")
