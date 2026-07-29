class InsufficientStockError(Exception):
    """
    Wird ausgelöst, wenn die angefragte Menge den verfügbaren Lagerbestand übersteigt.
    """
