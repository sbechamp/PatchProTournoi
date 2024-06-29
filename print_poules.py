import requests
import re
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


# méthodes utilitaires
def enlever_parentheses(chaine):
    # Remplace les parties entre parenthèses et les parenthèses elles-mêmes par une chaîne vide
    return re.sub(r'\([^)]*\)', '', chaine)


def increment_url(input_url):
    # Utilisation d'une expression régulière pour trouver la dernière partie numérique de l'URL
    match = re.search(r'(\d+)(?!.*\d)', input_url)
    if match:
        # Extraire la dernière partie numérique
        number = int(match.group(1))
        # Incrémenter la partie numérique
        incremented_number = number + 1
        # Remplacer l'ancienne partie numérique par la nouvelle
        new_url = input_url[:match.start(1)] + str(incremented_number) + input_url[match.end(1):]
        return new_url
    else:
        raise ValueError("L'URL ne contient pas de partie numérique.")


# méthodes pour construire l'export d'une page
def init(input_url):
    # Envoyer une requête GET à l'URL
    response = requests.get(input_url)
    if response.status_code != 200:
        raise Exception(f"Failed to load page {input_url}")
    # Analyser le contenu HTML de la page
    return BeautifulSoup(response.content, 'html.parser')


def trouve_titre(soup):
    for poule in soup.find_all('li', class_='active'):
        link = poule.find('a')  # Trouver la balise <a> à l'intérieur de l'élément
        if link and link.text.strip().startswith('Poule'):
            break
    return link


def ajoute_titre(soup, elements, styles):
    poule_link = trouve_titre(soup)
    poule_text = poule_link.text.strip()
    # Ajouter au PDF comme un titre
    title = Paragraph(poule_text, styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.2 * inch))


def ajoute_tableau_poule(soup, elements):
    # Trouver le tableau des poules
    poule_table = soup.find('table', {"class": "table table-vcenter table-hover table-bordered"})
    # Vérifiez si poule_table est None
    if poule_table is None:
        print(soup.prettify())
        raise Exception("Could not find the poule table on the page.")
    # Extraire les en-têtes du tableau
    headers = []
    for th in poule_table.find_all('th'):
        headers.append(th.text.strip())
    # Extraire les lignes du tableau
    rows = []
    for tr in poule_table.find_all('tr'):
        cells = tr.find_all('td')
        if len(cells) > 0:  # S'assurer que ce n'est pas une ligne d'en-tête
            row = [enlever_parentheses(cell.text.strip().replace('\n', '')) for cell in cells]
            rows.append(row)
    # Créer une liste de données pour le tableau PDF
    data = [headers] + rows
    row_heights = [18] * len(data)
    col_widths = [30, 100, 50, 50, 50, 50, 50, 50]
    table = Table(data, colWidths=col_widths, rowHeights=row_heights)
    # Ajouter un style au tableau
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Couleur de fond pour la première ligne (en-tête)
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # Couleur de texte pour la première ligne
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Alignement centré pour toutes les cellules
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Police en gras pour la première ligne (en-tête)
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Couleur de fond blanc pour les autres lignes
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Bordures autour de toutes les cellules
    ])
    table.setStyle(style)
    # Ajouter au PDF
    elements.append(table)


def ajoute_journees_matchs(soup, elements, styles):
    # Créer une liste pour stocker les informations des journées et des matchs
    journees = []
    # Trouver toutes les journées
    row_section_all = soup.find_all('div', class_='row')
    row_section_non_empty = [tag for tag in row_section_all if tag.find() is not None]
    for row_section in row_section_non_empty:
        journee_section = row_section.find('h3', class_='sub-header')
        if journee_section is not None:
            journee_title = journee_section.text.strip()
            matchs = []
        match_section = row_section.find_all('h3', class_='widget-content');
        if match_section is not None:
            i = 0
            for match in match_section:
                match_info = match.text.strip()
                if i % 2 == 0:
                    m = [match_info]
                else:
                    m.append(match_info)
                    matchs.append(m)
                i += 1
        if matchs:
            journees.append((journee_title, matchs))
    # styles des tableaux et de l'englobant
    style_match = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),  # Couleur de fond pour la première ligne (en-tête)
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),  # Couleur de texte pour la première ligne
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Alignement centré pour toutes les cellules
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Couleur de fond blanc pour les autres lignes
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Bordures autour de toutes les cellules
    ])
    table_main_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
    ])
    # Création de l'objet Table principale avec les tableaux
    for journee, matchs in journees:
        para = Paragraph(journee, styles["Heading2"])
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(para)
        i = 0
        for match in matchs:
            data_match = [
                [match[0], '    ', '    ', '    ', '    ', '    '],
                [match[1], '    ', '    ', '    ', '    ', '    ']]
            col_widths = [80, 27, 27, 27, 27, 27]
            table_match = Table(data_match, col_widths)
            table_match.setStyle(style_match)
            if i % 2 == 0:
                data_main = [[]]
                data_main[0].append(table_match)
            else:
                data_main[0].append(table_match)
                table_main = Table(data_main)
                table_main.setStyle(table_main_style)
                elements.append(table_main)
            i += 1


def creer_fichier_pdf(elements, pdf_file):
    document = SimpleDocTemplate(pdf_file, pagesize=letter)
    # Construire le PDF
    document.build(elements)


def creer_page_poule(url, elements):
    soup = init(url)
    styles = getSampleStyleSheet()
    ajoute_titre(soup, elements, styles)
    ajoute_tableau_poule(soup, elements)
    ajoute_journees_matchs(soup, elements, styles)


# main method
def export_poules(url, number_poules):
    soup = init(url)
    real_url = 'https://iframe.protournoi.fr/' + trouve_titre(soup).get('href')
    print(real_url)
    elements = []
    for i in range(1, number_poules + 1):
        if i > 1:
            elements.append(PageBreak());
        creer_page_poule(real_url, elements)
        real_url = increment_url(real_url)
    pdf_file = "poules.pdf"
    creer_fichier_pdf(elements, pdf_file)
    print(f"Les informations des poules ont été enregistrées dans {pdf_file}")


# Executable
# url = "https://iframe.protournoi.fr/app/competition/tournoi-ete-21-07-2023-tableau/matchs/99890/173450"
# bug

url="https://www.protournoi.fr/app/competition/tournoi-ete-21-07-2023-vvtt/matchs/99871/173420"
nb_poules = 8
export_poules(url, nb_poules)
