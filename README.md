# Flight Bot

Bot Telegram che cerca voli diretti a basso prezzo su Google Flights (tramite [SerpApi](https://serpapi.com/)) e li consulta per data, aeroporto di partenza o di arrivo.

Il progetto ha due parti indipendenti:

- **Scraper** (`retrieve_data.py`): scarica i voli del mese successivo e li salva in `data.json`. Pensato per girare una volta al mese da cron. A fine run manda su Telegram un riepilogo con i 5 voli più economici, oppure un avviso se qualcosa è andato storto.
- **Bot** (`app.py`): legge `data.json` e risponde ai comandi e ai pulsanti. Risponde solo all'utente configurato in `CHAT_ID`.

Limiti noti: solo voli di sola andata e solo voli diretti.

## Requisiti

- Python 3.10 o superiore e [uv](https://docs.astral.sh/uv/)
- Un bot Telegram: crealo con [@BotFather](https://t.me/BotFather) e copia il token
- Il tuo ID utente Telegram (puoi ottenerlo, ad esempio, da [@userinfobot](https://t.me/userinfobot))
- Una chiave API di SerpApi

## Configurazione

```bash
uv sync

cp .env.example .env
cp src/flight_bot/data.example.json src/flight_bot/data.json
```

Compila `.env`:

| Variabile   | Contenuto                                  |
|-------------|--------------------------------------------|
| `BOT_TOKEN` | Token del bot, da BotFather                |
| `CHAT_ID`   | Il tuo ID utente Telegram (solo cifre)     |
| `API_TOKEN` | Chiave API di SerpApi                      |

Modifica `src/flight_bot/data.json`. I filtri si possono cambiare anche dal bot con `/filters`:

| Chiave         | Significato                                                        |
|----------------|--------------------------------------------------------------------|
| `departure_id` | Codici IATA di partenza separati da virgola, es. `TRN,MXP,BGY`     |
| `arrival_id`   | Codici IATA di arrivo separati da virgola, es. `MAD,BCN,FCO`       |
| `max_price`    | Prezzo massimo per volo                                            |
| `currency`     | Valuta, es. `EUR`                                                  |
| `flights`      | Riempito dallo scraper, lascialo `{}`                              |

## Uso

Tutti i comandi vanno lanciati dalla cartella principale del progetto: i percorsi di `data.json` e `log.txt` sono relativi alla cartella corrente.

Avvio del bot:

```bash
uv run flight-bot
```

Scaricare i voli:

```bash
uv run src/flight_bot/retrieve_data.py
```

Comandi del bot:

| Comando    | Funzione                                         |
|------------|--------------------------------------------------|
| `/start`   | Avvia il bot                                     |
| `/filters` | Mostra e modifica partenze, arrivi e prezzo max  |
| `/search`  | Cerca per data, partenza o destinazione          |

Accanto a ogni data il bot mostra quando sono stati scaricati i prezzi: le date del mese corrente rimaste dal run precedente non vengono riscaricate e possono essere vecchie.

## Esecuzione automatica

Esempio di cron che lancia lo scraper il giorno 15 di ogni mese alle 03:00:

```
0 3 15 * * cd /percorso/del/progetto && /percorso/di/uv run src/flight_bot/retrieve_data.py >> cron.log 2>&1
```

Il `cd` è necessario, e conviene usare il percorso assoluto di `uv` perché nel cron il `PATH` è minimo.

Se tre date consecutive falliscono (per esempio perché i crediti SerpApi sono finiti) lo script si interrompe, esce con codice 1 e ti avvisa su Telegram. Le date non scaricate mantengono i dati precedenti.

## Costi

Ogni data richiede una chiamata a SerpApi per l'aeroporto di arrivo in prima posizione, più una chiamata ogni 10 aeroporti di arrivo successivi. Un run del mese costa quindi circa 30 × (1 + ⌈(arrivi − 1) / 10⌉) ricerche. Controlla che rientri nel tuo piano.

## Licenza

[MIT](LICENSE)