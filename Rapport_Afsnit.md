# Miniprojekt: Pointberegning i King Domino

## 1. Introduktion og Formål
Dette miniprojekt sigter mod at automatisere pointberegningen af afsluttede spilleplader i brætspillet King Domino. King Domino er et strategisk spil, hvor spillere bygger et 5x5 grid af dominobrikker bestående af forskellige terræntyper (bl.a. Forest, Field, Mine, Swamp, Lake og Grassland) og pointsamlende "kroner". 

Vores løsningsarkitektur deler opgaven op i tre specialiserede pipelines:
1. **Machine Learning Pipeline:** En klassifikationsmodel, der ud fra farvedistributioner og træk identificerer terræntypen for de 25 individuelle felter på spillepladen.
2. **Computer Vision Pipeline:** En template-matching algoritme, som lokaliserer og tæller antallet af pointgivende kroner.
3. **Algoritmisk Pipeline:** Et nabo-søgende regelsæt (Flood-fill), der samler ens terræner i lukkede områder (clusters) og udfører den underliggende matematik for spillets pointfordeling.

I det følgende gennemgås de implementerede metoder, de tekniske samt matematiske valg der ligger til grund for systemets udvikling, og endeligt en refleksion over mødte udfordringer under udviklingen af systemet.


## 2. Databehandling og Feature Extraction
For at maskinesystemet kan håndtere de rå spilleplader, isoleres hvert af spillepladens felter matematisk i et 2D grid på $5 \times 5$ felter. Systemet skærer systematisk det totale billede op i rektangulære `tiles` via list slicing (eksempelvis `image[y*100 : (y+1)*100, ...]`).

Hvert felt konverteres fra standard BGR (Blå, Grøn, Rød) til HSV (Hue, Saturation, Value) farverummet. Denne konvertering er udvalgt pga. dens robusthed overfor varierende lysforhold og skygger, som ellers kan manipulere med RGB-værdierne.
For at formidle feltets egenskaber struktureret til den efterfølgende machine learning-model, genereres en feature-vektor ud fra de tre HSV kanaler. Der udtages median-værdien for hver spektrum:
$$Med\text{-}Værdier = \{H_{median}, S_{median}, V_{median}\}$$

Dernæst trækkes der histogramegenskaber, hvor farvernes fordeling inddeles i intervaller (bins) af størrelsen 10. `Hue`-kanalen fordeles på intervaller fra 0-180, hvor `Saturation` og `Value` indeholder fordelinger af værdierne 0-255. 
Denne matematisk nedbrudte profilering genererer en dataset-række med i alt 74 detaljerede features pr. felt, som danner det statistiske fundament for genkendelsessystemet.


## 3. Machine Learning: Terrænklassificering
Til klassificeringen af de seks generiske terræntyper samt den farveløse "blank"-type, fungerer en *Random Forest Classifier* model som grundsten. Modellen er trænet på manuelle annotationer i tilhørende træningssæt via `LabelEncoder`, som tillader algoritmen at arbejde kvantitativt med tekst-strenge.

Random Forest-modellen er initieret med `100` individuelle beslutningstræer (estimators) og et `min_samples_split` på 10. Valget af Random Forest er understøttet af metodens udtalte styrke indenfor tabulær feature-data; den kan tildele stor vægt til vigtige features (eksempelvis tilstedeværelsen af højt udslag i grønne H-bins ved skov- og græsfelter), men tillader en samlet og udjævnet afstemning blandt de 100 træer, hvilket minimerer risikoen for ren overfitting på det begrænsede King Domino test- og træningsdata.


## 4. Computer Vision: Krone-detektion
Lokaliseringen af kroner indenfor hvert felt præsenterer en markant skalering- og rotationsudfordring, idet spilbrikkerne af spillerne kan roteres i flere retninger. Kronedetektionen løses gennem metoden *Normeret Krydskorrelation* (Normed Cross-Correlation) indenfor området Template Matching (`cv.TM_CCOEFF_NORMED`). 

En formskabelon af spillets point-kroner filtreres systematisk mod alle felterne ved et defineret korrelations-treshold på $0.70$.
For at opnå en matematisk rotation- og skalainvarians (hvor kronen findes uanset spillets fremtræden), itereres der asymmetrisk ad 50 inkrementale skaleringstrin ($s$) fra $1.0$ indskrænket ned til $0.20$.
For ethvert $s$-trin, anvendes matricetransformation der uafhængigt roterer formskabelonen med intervallerne $\theta = \{0^\circ, 90^\circ, 180^\circ, 270^\circ\}$.

Resultater samles af algoritmen ved at lokalisere alle templates, hvorved støj fjernes via `cv.groupRectangles`. Dette optimerer for falske positive resultater ved at konsolidere overlap og fjerne støjende gentagelser af en korrekt detekteret krone over de mange skala- og rotationsvaliderede templates.


## 5. Algoritmik: Pointberegnings logik
Sidste trin af opgaven varetages af det specialudviklede Point Calculator modul, hvilket evaluerer hele spillepladens 5x5 grid i samklang. Modulets funktion er at bygge "clusters", hvor identiske og tilstødende terræntyper grupperes i henhold til spillets love.

Her implementeres en rekursiv list-baseret `Flood Fill`-algoritme, der identificerer naboceller alene via vertikale og horisontale offsets (`x±1, y` og `x, y±1`). Diagonale offsets ($dx=\pm 1, dy=\pm 1$) er bevidst ekskluderet i henhold til de officielle King Domino spilleregler.
Hvert identificeret terræn forbliver ubesøgt indtil en nabosøgning igangsættes, hvori enhver korrekt nabo tilføjes felt-længden ($T_c$) og arver evt. kroneværdi ($K_c$) i dette lukkede område $c$. Derved danner den bagvedliggende pointmatematik spillets score:

$$ \text{Total Score} = \sum_{c \, \in \, \text{Clusters}} \left( T_c \times K_c \right) $$

Logikken leverer derved det samlede slutresultat samt returnerer fuldt regnskab for de gennemsøgte zoner, en feature specielt designet for manuel transparens og debugging af systemet.


## 6. Resultater og Refleksion (Diskussion)
Systemets performance i test er meget høj for afgrænsede moduler, eksempelvis fejler den matematiske Flood-Fill algoritme aldrig dens tiltænkte formål udregningsmæssigt. Modulet integreret med systemets Output giver os derimod indsigt og direkte transparens i modellens svagheder. 

F.eks forekommer der under test scenarier, hvor Random Forest modellen fejl-vurderer gule kornmarker (`Field`) som værende `Grassland` grundet et overlap i deres H-værdi og manglende kontrasttræning på baggrundene. I spillet tillader det, at Field-felter ukorrekt sammenlægges med reelt Grassland til store scoregivende clusters, der ødelægger systemets pointpræcisionen. Resultatet fastslår et fremtidigt behov for skarpere modeltræning ved at øge mængden af isolerede kornmarker i vores `Trainingset.xlsx`.

Yderligere falder "Template Matching"-metoden oftest igennem, hvis kronens baggrund i skabelonen møder kontrast på pladen, specielt over lyseblå markører (`Lake`). Skabelonen af en mørk krone falder markant i krydskorrelation imod lyseblå baggrunde til under de $0.70$. Det debatteres at implementere Alpha-gennemsigtighed gennem OpenCV (`cv.TM_CCORR_NORMED`) kombineret med en decideret maske for derved ud fra maske-laget alene at vurdere krone-kanterne kontra baggrundstrøj. Der er ligeledes overvejet brug af `Canny Edge Detection` til at ignorere baggrund og blot sammenligne kontur fremadrettet.
Disse erfaringer dokumenterer udfaldet af et system med mange bevægelige parametre og vidner om nødvendigheden af et fast forankret debug-regnskab på vej mod et færdigudviklet King Domino beregnerværktøj.