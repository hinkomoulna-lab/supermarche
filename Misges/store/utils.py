def montant_en_lettres(montant):
    if montant is None:
        return "Zéro FCFA"
    try:
        montant = int(round(float(montant)))
    except (ValueError, TypeError):
        return "Zéro FCFA"

    if montant == 0:
        return "Zéro FCFA"

    unites = ["", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf",
              "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize",
              "dix-sept", "dix-huit", "dix-neuf"]
    dizaines = ["", "", "vingt", "trente", "quarante", "cinquante", "soixante",
                "soixante-dix", "quatre-vingt", "quatre-vingt-dix"]

    def en_dessous_de_mille(n):
        result = ""
        if n >= 100:
            centaines = n // 100
            if centaines > 1:
                result += unites[centaines] + " cent"
            else:
                result += "cent"
            n %= 100
            if n > 0:
                result += " "
        if n > 0:
            if n < 20:
                result += unites[n]
            else:
                d = n // 10
                u = n % 10
                if d == 7 or d == 9:
                    result += dizaines[d - 1] + "-" + unites[10 + u]
                elif u == 0:
                    result += dizaines[d]
                elif u == 1:
                    result += dizaines[d] + " et un"
                else:
                    result += dizaines[d] + "-" + unites[u]
        return result.strip()

    resultat = ""
    if montant >= 1000000:
        millions = montant // 1000000
        if millions > 1:
            resultat += en_dessous_de_mille(millions) + " millions "
        else:
            resultat += "un million "
        montant %= 1000000
    if montant >= 1000:
        milliers = montant // 1000
        if milliers > 1:
            resultat += en_dessous_de_mille(milliers) + " mille "
        else:
            resultat += "mille "
        montant %= 1000
    if montant > 0:
        resultat += en_dessous_de_mille(montant)

    return resultat.strip().capitalize() + " FCFA"
