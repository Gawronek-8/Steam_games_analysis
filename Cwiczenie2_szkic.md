# Ćwiczenie 2 – szkic

## Zadanie

### 1. Wczytanie danych i wstępna analiza

- Zaimportuj wszystkie wybrane źródła danych.
- Przejrzyj strukturę (liczba kolumn, typy danych, unikalne wartości).
- Zanotuj, które kolumny mogą pełnić rolę kluczy łączących (np. data, ID, lokalizacja).
- Zwróć uwagę na ewentualne problemy: brakujące dane, różne formaty, niejednolite nazwy.
- Zanotuj i udokumentuj wszystkie zauważone elementy w raporcie.

### 2. Profilowanie jakości danych

- Oceń jakość danych – czy są kompletne, spójne, aktualne, poprawne.
- Opisz, jakie błędy lub nieścisłości się pojawiają (np. puste pola, niepoprawne jednostki, duplikaty, niespójne nazwy).
- Zanotuj, jakie kroki naprawcze mogą być potrzebne (np. konwersja formatu dat, ujednolicenie jednostek, uzupełnienie braków).
- Przygotuj prosty słownik danych (Data Dictionary) z opisem tabel i kolumn (nazwa, typ, znaczenie, źródło, uwagi).
- Stwórz krótki opis reguł jakości danych (Data Quality Rules), które będą sprawdzane lub egzekwowane w kolejnych etapach.
- Zanotuj i udokumentuj wszystkie zauważone elementy w raporcie.

### 3. Łączenie danych i koncepcja modelu

- Zidentyfikuj wspólne pola, które umożliwią połączenie źródeł (JOIN).
- Zaplanuj wstępny schemat modelu danych – może to być prosty diagram pokazujący relacje między tabelami (np. model gwiazdy: tabela faktów + tabele wymiarów).
- Połącz dane, wykorzystując relacje (np. fakty → wymiary).
- Jeżeli dane wymagają mapowania (np. miasta → regiony), utwórz dodatkową tabelę pomocniczą.
- Zanotuj i udokumentuj wszystkie zauważone elementy w raporcie.

---

## 1. Wczytanie danych i wstępna analiza
Tabele:
- steam_top_games - 78 kolumn, opis najważniejszych kolumn (dane wstępnie zduplikowane, gry pobierano względem popularności, która w czasie pobierania danych się zmieniała):
    1. appid - klucz prywatny, wskazuje jednoznacznie o jakiej grze mowa
    2. display_name - nazwa gry, przydatne przy jednostkowych ocenach gier (wersja ocenzurowana)
    3. name - nazwa gry, przydatne przy jednostkowych ocenach gier
    4. reviews.summary_filtered.review_count - liczba recenzji graczy
    5. reviews.summary_filtered.percent_positive - procent pozytywnych recenzji
    6. reviews.summary_filtered.review_score - numeryczna ocena pozytywnych opinii, 0 oznacza niewryustarczającą liczbę opinii
    7. reviews.summary_filtered.review_score_label - słowa ocena pozytywnych opinii, w przypadku zera określa liczbę opinii
    8. release.steam_release_date - data wydania, podana w sekundach, dotyczy systemu windows, istnieją kolumny dla mac i linux, lecz są wybrakowane w ogromnym stopniu
    9. UWAGI
    10. Pozostałe kolumny dotyczą między innymi opcji sprzedaży, na przykład w jakim pakiecie najlepiej kupić grę itp, co nie ma wpływu na analizę
    11. Kolumny związane z tagami i kategoriami istnieją, lecz w formie listy i zostały przekształcone do tabeli przechodniej, wiążącej daną grę z danym tagiem 
- steam_upcoming_games - 58 kolumn, opis najważniejszych (dane wstępnie zduplikowane, gry pobierano względem popularności, która w czasie pobierania danych się zmieniała):
    1. appid - klucz prywatny, wskazuje jednoznacznie o jakiej grze mowa
    2. display_name - nazwa gry, przydatne przy jednostkowych ocenach gier (wersja ocenzurowana)
    3. name - nazwa gry, przydatne przy jednostkowych ocenach gier
    4. release.steam_release_date - data wydania, podana w sekundach i dotyczy systemu windows, większość gier nie podaje konkretnej daty wydania i wartość jest wtedy ustawiona jako null, 
    5. release.coming_soon_display - informuje o stanie daty wydawanwej gry, przyjmuje kilka opcji i dytkuje rozumienie kolumny 4., m.in. wartość date_year podaje rok, kiedy gra zostanie wydana, wtedy kolumna 4. oznacza rok w sekundach
    6. release.original_release_date - oryginalna data wydania, znaczenie nie do końca jasne, patrz w uwagi
    6. UWAGI
    7. Pozostałe kolumny dotyczą między innymi opcji sprzedaży, na przykład w jakim pakiecie najlepiej kupić grę itp, co nie ma wpływu na analizę
    8. Kolumny związane z tagami i kategoriami istnieją, lecz w formie listy i zostały przekształcone do tabeli przechodniej, wiążącej daną grę z danym tagiem
    9. RĘCZNA WERYFIKACJA POKAZAŁA, ŻE CZĘŚĆ GIER NIE WYJDZIE NIGDY, CZĘŚĆ GIER MA DATĘ WYPUSZCZENIA USTAWIONĄ NA TAKĄ, KTÓRA WYPADŁA, LECZ GRA DALEJ NIE WYSZŁA, CZĘŚĆ GIER MA DATĘ USTAWIONĄ NA NAPRZYKŁAD 2077, NIEKTÓRE GRY WYSZŁY ALE PRAWDOPODOBNIE ZOSTAŁY COFNIĘTE (KURATORZY STEAM OCENILI GRĘ, KTÓRA NIE WYSZŁA), DO EKSPLORACJI DANYCH UŻYTO RÓWNIEŻ KOLUMNY release.original_release_date, CZASEM JEST ONA PODANA, CZASEM USTAWIONA NA PRZESZŁOŚĆ - PRAWDOPODOBNIE GRA NIE ZOSTANIE WYDANA NIGDY - RZADKO ZAZĘBIENIE Z PLANOWANĄ DATĄ WYDANIA 
- steam_tags - 3 kolumny, opis najważniejszych:
    1. tagid - id tagu, który rozróżnia go od innych
    2. name - co oznacza dany tag, głównie odnośnie gatunku gry, np. RPG, Racing, ale również Free to play
- steam_categories - 10 kolumn, opis najważniejszych:
    1. categoryid - id kategorii, która wyróżnia go od innych
    2. display_name - co oznacza dana kategoria
    3. type - typ kategorii, wartości 0-4, 1 oznacza rodzaj gry, single/multiplayer itp, 2 obsługiwane funkcje, np achievementy, 3 obsługa kontrolerów, 0 - rodzaj produktu, demo, dlc itp
- steam_upcoming_games_tags, steam_upcoming_games_categories, steam_top_games_tags, steam_top_games_categories, każda po 2 kolumny, tabele pośrednie, łączące tagi i kategorie z grami
- censored_words - 1 kolumna:
    1. censored_words - kolumna zawierające obraźliwe słowa, które znajdują się w nazwie gry, wykorzystana do stworzenia kolumn display_name dla tabel z grami
- steam_current_prices - 8 kolumn:
    1. appid - id gry, której cena dotyczy
    2. country_code - kod kraju, którego cena dotyczy, kod dwuznakowy
    3. currency - waluta, w której podawana jest cena
    4. price - cena finałowa po możliwej obniżce (dane z konkretnej daty, zwracają aktualną cenę, w tym po zniżce)
    5. initial - aktualna cena bez obniżki
    6. price_dsc - wartość zniżki o ile występuje
    7. status - 3 wartości, priced, not available, no_price, kolumna stworzona na etapie pobierania danych w pythonie, oznacza czy gra jest free to play, czy ma cenę, czy jest niedostępna w danym kraju 
- itad_price_history - 11 kolumn, historia zmian cen gier na Steam z IsThereAnyDeal, 7000 najpopularniejszych gier dla 10 krajów (PL, DE, FR, ES, US, JP, AR, TR, CH, CN), od 01.01.2023, jeden wiersz to jedna zmiana ceny, opis najważniejszych:
    1. app_id - id gry ze Steam, klucz łączący z tabelami gier (appid)
    2. country - kod kraju, którego cena dotyczy, kod dwuznakowy, taki sam jak w steam_current_prices
    3. timestamp - data i godzina zmiany ceny, ze strefą czasową (np. +02:00)
    4. currency - waluta, w której podawana jest cena
    5. regular_price - cena bazowa (bez zniżki) w momencie zmiany
    6. cut - wartość zniżki w %, 0 oznacza cenę bez promocji (koniec promocji lub zmiana ceny bazowej)
    7. deal_price - cena po zniżce
    8. UWAGI 
    9. zakres danych różni się między krajami: DE, FR, ES, CH, US, TR, CN od 2023-01, JP od 2024-12, PL i AR dopiero od 2026-01, pierwszy wpis z datą 2023-01-01 to stan ceny na początek okresu, a nie zmiana ceny
    10. gry, których nie ma w bazie ITAD, mają jeden wiersz z samym app_id, itad_id i krajem, reszta pusta
    11. w Turcji występują ceny zarówno w TRY, jak i w USD (przejście na USD w 2023)
- nbp_rates_table_A - 7 kolumn, średnie kursy walut NBP, publikowane w każdy dzień roboczy od 02.01.2023, jeden wiersz to waluta w danym dniu, opis najważniejszych:
    1. effectiveDate - data, której dotyczy kurs
    2. code - kod waluty np. USD, EUR
    3. mid - średni kurs, ile PLN kosztuje 1 jednostka waluty
    4. currency - nazwa waluty po polsku
    5. UWAGI 
    6. brak PLN (kurs równy 1)
- nbp_rates_table_B - 7 kolumn, te same kolumny co w tabeli A, rzadziej używane waluty, publikowane raz w tygodniu od 04.01.2023:
    1. UWAGI
    2. potrzebna dla walut ze Steam, których nie ma w tabeli A
- worldbank_gdp_per_capita_ppp - 11 kolumn, PKB per capita według parytetu siły nabywczej (PPP), wszystkie kraje dla lat 1960-2025, jeden wiersz to kraj w danym roku, opis najważniejszych:
    1. country.id - kod kraju, dwuznakowy, taki sam jak country_code w danych ze Steam, klucz łączący
    2. countryiso3code - kod kraju, trzyznakowy
    3. country.value - nazwa kraju po angielsku
    4. date - rok, którego dotyczy wartość
    5. value - PKB per capita PPP w dolarach międzynarodowych
    6. UWAGI 
    7. oprócz krajów zawiera agregaty 
    8. część krajów nie ma wartości dla najnowszych lat, jak i dla najstarszych
    9. z 41 krajów pobranych ze Steam brakuje tylko Tajwanu (TW), który nie jest w danych Banku Światowego
- worldbank_gni_per_capita_ppp - 11 kolumn, te same kolumny co dla PKB, wskaźnik DNB per capita PPP (dochód narodowy brutto):
    1. UWAGI
    2. alternatywa dla PKB przy liczeniu dostępności cenowej, do decyzji, którego wskaźnika używamy
- worldbank_countries - 19 kolumn, lista krajów i agregatów Banku Światowego, opis najważniejszych:
    1. iso2Code - kod kraju, dwuznakowy
    2. id - kod kraju, trzyznakowy
    3. name - nazwa kraju po angielsku
    4. region.value - region świata, dla agregatów wartość Aggregates, pozwala odfiltrować agregaty
    5. incomeLevel.value - grupa dochodowa kraju np. High income, Upper middle income


## 2. Profilowanie jakości danych

### Ocena jakości

- kompletność:
    1. steam_top_games - Duplikaty spowodowane zmieniającą się popularnością podczas pobierania - w celu pobrania najbardziej popularnych gier, użyto w query opcji sort=10, co oznacza pobieranie gier z dynamicznej listy gier najpopularniejszych
    2. steam_upcoming_games - duplikaty, powód jak wyżej, większość wierszy nie ma podanej daty premiery, niektóre mają podany rok, inne mieisąc i rok, a niewielka część ma dokładną datę - stworzenie kolumny określającej dokładność daty wydania
    4. steam_current_prices - Część gier jest niedostępna w niektórych państwach
    5. itad_price_history - 7000 gier dla 10 krajów, ale zakres historii różni się między krajami (PL i AR dopiero od 2026-01, JP od 2024-12), część gier nie występuje w bazie ITAD
    6. worldbank_gdp_per_capita_ppp - Niektóre kraje nie posiadają danych na rok 2025, usunięto takie wiersze, ocena będzie dokonywana na najbliższym roku do roku 2026 w danym kraju
    7. tabele A i B nbp - tabela B zawiera więcej walut, ale dla niej wyniki są rzadziej prezentowane - 1 w tygodniu, tabela A ma dane odświeżane codziennie, lecz dla mniejszej ilości krajów
- spójność:
    1. kody krajów są dwuznakowe we wszystkich źródłach, dzięki czemu tabele można łączyć bez mapowania kodów
    2. kody walut w danych ze Steam i ITAD są takie same jak w tabelach NBP
    3. ceny w Argentynie i Turcji są podawane w USD, w historii ITAD dla Turcji występują zarówno TRY, jak i USD
    4. część kategorii ma tę samą nazwę, ale różne id (np. Steam Workshop 30 i 51, DualShock 55 i 56, DualSense 57 i 58)
    5. część nazw regionów w worldbank_countries ma spację na końcu (np. "Latin America & Caribbean ")
- aktualność:
    1. dane są zrzutem z konkretnego dnia: gry 26.10.2026, historia cen ITAD do 27.10.2026, ceny bieżące 15-16.11.2026, kursy NBP do 16.11.2026
    3. dane Banku Światowego są roczne, najnowszy pełny rok to 2024, rok 2025 jest niekompletny
- poprawność:
    1. część dat premiery to wartości zastępcze, 0 sekund (01.01.1970, 16 gier w top, 2 w nadchodzących) oraz daty typu 2104 w grach nadchodzących
    2. niektóre gry mają datę wydania z przeszłości, lecz jeszcze nie wyszły
    3. dla niepełnych dat premiery (miesiąc, kwartał, rok) Steam podaje ostatni dzień okresu, np. dla date_year 31.12 danego roku
    4. pierwszy wpis w historii ITAD z datą 2023-01-01 to stan ceny na początek okresu, a nie zmiana ceny

### Błędy i nieścisłości

- steam_top_games, steam_upcoming_games:
    1. duplikaty gier, ta sama gra pojawia się kilka razy, bo zmieniała pozycję w rankingu w trakcie pobierania
    2. data premiery zapisana w sekundach od 01.01.1970, a nie jako data
    3. dwie daty premiery, jedna mylna i nieprzydatna w większości - original_release_date
    4. data premiery gier nadchodzących ma różną dokładność (dzień, miesiąc, kwartał, rok lub brak), zależną od kolumny release.coming_soon_display
    5. tagi i kategorie zapisane jako lista w jednej komórce, kategorie dodatkowo w 3 osobnych kolumnach (tryb gry, funkcje, kontrolery)
    6. nazwy części gier zawierają obraźliwe słowa
    7. bardzo duża liczba kolumn (78 i 58), z czego większość nie jest potrzebna w analizie
- steam_upcoming_games_tags, steam_top_games_tags, steam_upcoming_games_categories, steam_top_games_categories:
    1. powtórzone pary gra - tag / gra - kategoria, przeniesione z duplikatów gier
- steam_current_prices:
    1. brak ceny w części wierszy z trzech różnych powodów: gra darmowa, gra niedostępna w danym kraju 
    2. ceny w różnych walutach, bez przeliczenia na wspólną walutę
- itad_price_history:
    1. wiersze z samymi kluczami (app_id, itad_id, country) i pustymi pozostałymi kolumnami dla gier, których nie ma w bazie ITAD
    2. data zmiany ceny ze strefą czasową (np. +02:00)
    3. różny zakres historii w zależności od kraju
- nbp_rates_table_A, nbp_rates_table_B:
    1. brak kursów w weekendy i święta, w tabeli B kurs tylko raz w tygodniu
- worldbank_gdp_per_capita_ppp, worldbank_gni_per_capita_ppp, worldbank_countries:
    1. kraje wymieszane z agregatami (regiony, grupy dochodowe)

### Kroki naprawcze

- wykonane:
    1. usunięcie duplikatów gier w Power Query (Usuń duplikaty) po kolumnie appid
    2. tagi i kategorie przekształcone skryptem w Pythonie do tabel pośrednich (game_id, tag_id / category_id), 3 kolumny kategorii połączone w jedną tabelę, grupa kategorii jest w steam_categories (kolumna type)
    3. stworzenie kolumny display_name z nazwą gry, w której obraźliwe słowa z tabeli censored_words zastąpiono znakami # (tyle znaków, ile liter w słowie)
    4. zamiana daty premiery z sekund na datę (kolumna niestandardowa), wartości 0 zamienione na null
    5. dodanie kolumny release_precision dla gier nadchodzących (day, month, quarter, year, null), na jej podstawie analizy terminu premiery są robione na poziomie nie dokładniejszym niż dokładność daty
    6. dodanie kolumn status (priced, no_price, not_available) do steam_current_prices na etapie pobierania danych w Pythonie, na podstawie surowej odpowiedzi Steam
    7. stworzenie dwóch tabel kalendarza: Kalendarz (2023-2027) dla historii cen i Kalendarz_premier (1970-2104) dla dat premiery
    8. usunięte nieużywane kolumny w tabelach gier
    9. usunięcie nieużywanych kolumn z tabel gier
    10. usunięcie powtórzonych par w tabelach pośrednich (Usuń duplikaty)

- do wykonania:
    1. tabela pomocnicza kraje: kraje z worldbank_countries bez agregatów, z przyciętymi nazwami regionów i dodanym Tajwanem
    2. przeliczenie cen na USD kursem NBP z dnia ceny (dla dni bez kursu ostatni wcześniejszy kurs), z użyciem waluty z każdego wiersza osobno (ważne dla Turcji)
    3. usunięcie z historii ITAD pustych wierszy gier, których nie ma w bazie ITAD, oraz zamiana timestamp na datę

### Data Dictionary



### Data Quality Rules



## 3. Łączenie danych i koncepcja modelu

### Klucze łączące



### Schemat modelu



### Tabele pomocnicze



