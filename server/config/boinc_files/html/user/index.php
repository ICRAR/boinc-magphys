<?php
// This file is part of BOINC.
// http://boinc.berkeley.edu
// Copyright (C) 2008 University of California
//
// BOINC is free software; you can redistribute it and/or modify it
// under the terms of the GNU Lesser General Public License
// as published by the Free Software Foundation,
// either version 3 of the License, or (at your option) any later version.
//
// BOINC is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
// See the GNU Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with BOINC.  If not, see <http://www.gnu.org/licenses/>.

// This is a template for your web site's front page.
// You are encouraged to customize this file,
// and to create a graphical identity for your web site
// my developing your own stylesheet
// and customizing the header/footer functions in html/project/project.inc

require_once("../inc/db.inc");
require_once("../inc/util.inc");
require_once("../inc/news.inc");
require_once("../inc/cache.inc");
require_once("../inc/uotd.inc");
require_once("../inc/sanitize_html.inc");
require_once("../inc/text_transform.inc");
require_once("../project/project.inc");

check_get_args(array());

function show_nav() {
    $config = get_config();
    $master_url = parse_config($config, "<master_url>");
    $no_computing = parse_config($config, "<no_computing>");
    $no_web_account_creation = parse_bool($config, "no_web_account_creation");
    $user = get_logged_in_user();
    echo "<div class=\"mainnav\">
        <h2 class=headline>About ".PROJECT."</h2>
    ";
    if ($no_computing) {
        echo "
            theSkyNet POGS is a research project that uses volunteers
            to do research in astronomy.
We will combine the spectral coverage of GALEX, Pan-STARRS1, and WISE to generate a multi-wavelength UV-optical-NIR galaxy atlas for the nearby Universe.
We will measure physical parameters (such as stellar mass surface density, star formation rate surface density, attenuation, and first-order star formation history) on a resolved pixel-by-pixel basis using spectral energy distribution (SED) fitting techniques in a distributed computing mode.
        ";
    } else {
        echo "

    <ul id=\"tabs\">
      <li><a href=\"#english\">English</a></li>
      <li><a href=\"#french\">Français</a></li>
      <li><a href=\"#russian\">Русский</a></li>
      <li><a href=\"#german\">Deutsch</a></li>
      <li><a href=\"#italian\">Italiano</a></li>
      <li><a href=\"#chinese\">中文</a></li>
      <li><a href=\"#polish\">Polski</a></li>
    </ul>

    <div class=\"tabContent\" id=\"english\">
TheSkyNet POGS is a research project that uses Internet-connected computers to do research in astronomy. We will combine the spectral coverage of GALEX, Pan-STARRS1, and WISE to generate a multi-wavelength UV-optical-NIR galaxy atlas for the nearby Universe. We will calculate physical parameters such as: star formation rate, stellar mass of the galaxy, dust attenuation, and total dust mass of a galaxy; on a pixel-by-pixel basis using spectral energy distribution fitting techniques. You can participate by downloading and running a free program on your computer.
<p><a href=\"http://www.theskynet.org\">TheSkyNet</a> is an initiative of the International Centre for Radio Astronomy Research (ICRAR), a joint venture of Curtin University and The University of Western Australia. 
By joining this project your computer will help astronomers around the world answer some of the big questions we have about the Universe. 
TheSkyNet POGS is theSkyNet's newest project, in testing since late 2012 and officially joining theSkyNet on our second birthday - September 13th 2013. 


    </div>

    <div class=\"tabContent\" id=\"french\">
theSkyNet POGS est un projet de recherche qui utilise des ordinateurs
connectés à internet afin d'effectuer de la recherche en astronomie. Notre
but est de combiner les couvertures spectrales de GALEX, Pan-STARRS1 et
WISE afin de produire un atlas de galaxies de l'Univers proche dans les
longueurs d'onde ultraviolet, optique et proche infrarouge. Nous
mesurerons leurs paramètres physiques (comme le taux de formation
stellaire, la masse stellaire de la galaxie, l'absorption causée par la
poussière interstellaire ainsi que sa masse totale dans la galaxie) pixel
par pixel grâce aux techniques de distribution spectrale d'énergie. Pour
participer, il vous suffit de télécharger puis lancer un programme gratuit
sur votre ordinateur.
<p>
<a href=\"http://www.theskynet.org\">TheSkyNet</a> est une initiative du Centre International de Recherche en Radioastronomie (ICRAR), et une entreprise commune entre les universités de Curtin et d'Australie Occidentale. En participant à ce projet, votre ordinateur servira à aider les astronomes du monde entier à répondre à quelques-unes des Grandes questions que nous nous posons sur notre univers. Le SkyNet POGs est le tout nouveau projet de theSkyNet, en phase de test depuis fin 2012 et y faisant officiellement part entière au deuxième anniversaire de theSkyNet le 13 Septembre 2013.
    </div>

    <div class=\"tabContent\" id=\"russian\">
theSkyNet POGS - это астрономический исследовательский проект, который использует компьютеры подключенные к Интернету для обработки данных с различных телескопов мира в разных диапазонах электромагнитного спектра. Мы объединяем GALEX, Pan-STARRS1 и WISE, чтобы создать многочастотный (ультрафиолетовый-оптический-инфракрасный спектры) атлас ближних к нам окрестностей вселенной. Мы определяем физические параметры (звездная масса галактик, поглощение излучения пылью, масса пылевой компоненты, скорость образования звезд) для каждого пиксела, используя технику поиска оптимума для распределения спектральной энергии. Вычисления для различных пикселов изображения распределяются между многими компьютерами подключенными к сети. Вы можете принять участие в нашей исследовательской программе скачав и запустив  бесплатную программу на вашем компьютере.
<p>
theSkyNet POGS разработан и координируется Международным Исследовательским Центром Радиоастрономический Исследований, Австралия, Перт.   
 </div>

<div class=\"tabContent\" id=\"german\">
theSkyNet POGS ist ein wissenschaftliches Projekt, das Computer im Internet dazu verwendet astronomische Forschung zu betreiben. Wir werden die Beobachtungen von GALEX, Pan-STARRS1 und WISE in unterschiedlichen Wellenlängenbereichen dazu verwenden einen Galaxien-Atlas des nahegelegenen Universums in den Spektralbereichen UV, optisch und nah-infrarot, zu erstellen. Wir werden physikalische Parameter berechnen, wie zum Beispiel die Sternentstehungsrate, die stellare und totale Galaxienmasse oder die Lichtabschwächung durch Staub. Diese Berechnungen werden mittels mathematischer Fitting-Technologien der Spektral-Energieverteilungen in jedem Pixel durchgeführt. Sie können das POGS Projekt unterstützen, indem sie ein kostenloses Programm herunterladen und auf ihrem Computer ausführen.
<p>
theSkyNet POGS ist ein Projekt des International Centre for Radio Astronomy Research (Internationales Zentrum für Radio Astronomische Forschung).

    </div>

    <div class=\"tabContent\" id=\"chinese\">
theSkyNet POGS 是一个利于互联网上的计算机来承担天文科研的研究项目。我们将合并若干个天文台（GALEX，Pan-STARRS1，WISE）的光谱范围，生成一个多波长的近宇宙 紫外-可见光-近红外 星系图集。我们将用光谱能量分布拟合技术从一个个像素上计算若干物理参数
（例如恒星形成率，星系恒星质量，尘埃衰减，星系尘埃总质量）。加入该项目，请下载免费的程序并在您的电脑运行。
<p>
theSkyNet POGS项目是由国际射电天文学研究中心发起的。
    </div>
    <div class=\"tabContent\" id=\"italian\">
TheSkyNet POGS é un progetto sperimentale che utilizza calcolatori connessi via Internet per condurre ricerca in astronomia. Le gamme spettrali di GALEX, Pan-STARRS1 e WISE verranno combinate per generare un atlante dell'universo vicino che copra molteplici lunghezze d'onda (ultravioletto-ottico-vicino infrarosso). Con tale ricerca, sara' possibile misurare diversi parametri fisici, per es.: tasso di formazione stellare, massa stellare nelle galassie, attenuazione indotta dalla polvere cosmica e contenuto di polvere cosmica interstellare nelle galassie. Tali parametri verrano estrapolati con risoluzione a livello di singolo pixel, utilizzando il metodo della distribuzione spettrale d'energia (SED) tramite tecniche di 'fitting'. Puoi partecipare anche Tu scaricando ed eseguendo un programma gratuito sul tuo computer.
<p>
The SkyNet POGS e' un progetto gestito dal Centro Internazionale della Ricerca in Radio Astronomia (International Centre for Radio Astronomy Research - ICRAR).
    </div>
    <div class=\"tabContent\" id=\"polish\">
TheSkyNet POGS jest projektem badawczym, który wykorzystuje komputery podłączone do Internetu, aby wykonywać badania w zakresie astronomii. Łączymy badania zakresu widma GALEX, Pan-STARRS1 i WISE, aby wygenerować Atlas pobliskiego wszechświata w zakresie fal UV - NIR. Będziemy obliczać parametry fizyczne, takie jak: prędkość formowania się gwiazd, gwiezdna masa galaktyk, tłumienie pyłu, i masa całkowita pyłu galaktycznego, przy użyciu metody pixel- po - pixelu i technik dopasowania spektralnej dystrybucji energii. Możesz zostać uczestnikiem badań pobierając i uruchamiając bezpłatny program na swoim komputerze.
<p>
<a href=\"http://www.theskynet.org\">TheSkyNet</a> to inicjatywa International Centre for Radio Astronomy Research (ICRAR), we współpracy z Curtin University i University of Western Australia. Przystępując do tego projektu, twój komputer pomoże astronomom na całym świecie odpowiedzieć na niektóre z wielkich pytań na temat Wszechświata. TheSkyNet POGS jest najnowszym projektem theSkyNet, testowanym do końca 2012 roku i oficjalnie włączonym do theSkyNet w nasze drugie urodziny - 13 września 2013
    </div>
        ";
    }
    echo "
        <ul>
	<li> <a href=\"http://www.theskynet.org/boinc/".$user->id."/galaxies\">Images you have processed</a>
        <li> <a href=\"http://www.theskynet.org/galaxies\">Images for all the Galaxies used in the survey</a>
        <li> <a href=\"http://www.theskynet.org/pages/Spectral%20Energy%20Distribution%20Fitting\">The Science we are trying to achieve</a>
        <li> <a href=\"http://www.theskynet.org/pages/team_pogs\">The Team</a>
        </ul>
        <h2 class=headline>Join ".PROJECT."</h2>
        <ul>
    ";
    if ($no_computing) {
        echo "
            <li> <a href=\"create_account_form.php\">Create an account</a>
        ";
    } else {
        echo "
            <li><a href=\"info.php\">".tra("Read our rules and policies")."</a>
            <li> This project uses BOINC.
                If you're already running BOINC, select Add Project.
                If not, <a target=\"_new\" href=\"http://boinc.berkeley.edu/download.php\">download BOINC</a>.
            <li> When prompted, enter <br><b>".$master_url."</b>
        ";
        if (!$no_web_account_creation) {
            echo "
                <li> If you're running a command-line version of BOINC,
                    <a href=\"create_account_form.php\">create an account</a> first.
            ";
        }
        echo "
            <li> If you have any problems,
                <a target=\"_new\" href=\"http://boinc.berkeley.edu/wiki/BOINC_Help\">get help here</a>.
        ";
    }
    echo "
        </ul>

        <h2 class=headline>Returning participants</h2>
        <ul>
    ";
    if ($no_computing) {
        echo "
            <li><a href=\"bossa_apps.php\">Do work</a>
            <li><a href=\"home.php\">Your account</a> - view stats, modify preferences
            <li><a href=\"team.php\">Teams</a> - create or join a team
        ";
    } else {
        echo "
            <li><a href=\"home.php\">Your account</a> - view stats, modify preferences
            <li><a href=server_status.php>Server status</a>
            <li><a href=\"team.php\">Teams</a> - create or join a team
            <li><a href=\"cert1.php\">Certificate</a>
            <li><a href=\"apps.php\">".tra("Applications")."</a>
        ";
    }
    echo "
        </ul>
        <h2 class=headline>".tra("Community")."</h2>
        <ul>
        <li><a href=\"profile_menu.php\">".tra("Profiles")."</a>
        <li><a href=\"user_search.php\">User search</a>
        <li><a href=\"forum_index.php\">".tra("Message boards")."</a>
        <li><a href=\"forum_help_desk.php\">".tra("Questions and Answers")."</a>
        <li><a href=\"stats.php\">Statistics</a>
        <li><a href=language_select.php>Languages</a>
        </ul>
        </div>
    ";
}

$stopped = web_stopped();
$rssname = PROJECT . " RSS 2.0" ;
$rsslink = URL_BASE . "rss_main.php";

header("Content-type: text/html; charset=utf-8");

echo "<!DOCTYPE html PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\" \"http://www.w3.org/TR/html4/loose.dtd\">";

echo "<html>
    <head>
    <title>".PROJECT."</title>
    <link rel=\"stylesheet\" type=\"text/css\" href=\"main.css\" media=\"all\" />
    <link rel=\"stylesheet\" type=\"text/css\" href=\"".STYLESHEET."\">
    <link rel=\"alternate\" type=\"application/rss+xml\" title=\"".$rssname."\" href=\"".$rsslink."\">
<style type=\"text/css\">
  ul#tabs { list-style-type: none; margin: 30px 0 0 0; padding: 0 0 0.3em 0; }
  ul#tabs li { display: inline; }
  ul#tabs li a {  border: 1px solid #c9c3ba; border-bottom: none; padding: 0.3em; text-decoration: none; }
  ul#tabs li a:hover { background-color: #f1f0ee; }
  ul#tabs li a.selected { color: #000; background-color: #f1f0ee; font-weight: bold; padding: 0.7em 0.3em 0.38em 0.3em; }
  div.tabContent { border: 1px solid #c9c3ba; padding: 0.5em;  }
  div.tabContent.hide { display: none; }
</style>

<script type=\"text/javascript\">
    //<![CDATA[

    var tabLinks = new Array();
    var contentDivs = new Array();

    function init() {

      // Grab the tab links and content divs from the page
      var tabListItems = document.getElementById('tabs').childNodes;
      for ( var i = 0; i < tabListItems.length; i++ ) {
        if ( tabListItems[i].nodeName == \"LI\" ) {
          var tabLink = getFirstChildWithTagName( tabListItems[i], 'A' );
          var id = getHash( tabLink.getAttribute('href') );
          tabLinks[id] = tabLink;
          contentDivs[id] = document.getElementById( id );
        }
      }

      // Assign onclick events to the tab links, and
      // highlight the first tab
      var i = 0;

      for ( var id in tabLinks ) {
        tabLinks[id].onclick = showTab;
        tabLinks[id].onfocus = function() { this.blur() };
        if ( i == 0 ) tabLinks[id].className = 'selected';
        i++;
      }

      // Hide all content divs except the first
      var i = 0;

      for ( var id in contentDivs ) {
        if ( i != 0 ) contentDivs[id].className = 'tabContent hide';
        i++;
      }
    }

    function showTab() {
      var selectedId = getHash( this.getAttribute('href') );

      // Highlight the selected tab, and dim all others.
      // Also show the selected content div, and hide all others.
      for ( var id in contentDivs ) {
        if ( id == selectedId ) {
          tabLinks[id].className = 'selected';
          contentDivs[id].className = 'tabContent';
        } else {
          tabLinks[id].className = '';
          contentDivs[id].className = 'tabContent hide';
        }
      }

      // Stop the browser following the link
      return false;
    }

    function getFirstChildWithTagName( element, tagName ) {
      for ( var i = 0; i < element.childNodes.length; i++ ) {
        if ( element.childNodes[i].nodeName == tagName ) return element.childNodes[i];
      }
    }

    function getHash( url ) {
      var hashPos = url.lastIndexOf ( '#' );
      return url.substring( hashPos + 1 );
    }

    //]]>
</script>

";
include 'schedulers.txt';
echo "
    </head><body onload=\"init()\">
<div id=\"fb-root\"></div>
<script>(function(d, s, id) {
  var js, fjs = d.getElementsByTagName(s)[0];
  if (d.getElementById(id)) return;
  js = d.createElement(s); js.id = id;
  js.src = \"//connect.facebook.net/en_US/all.js#xfbml=1\";
  fjs.parentNode.insertBefore(js, fjs);
}(document, 'script', 'facebook-jssdk'));</script>
    <div class=page_title>".PROJECT."</div>
    <div>
        <a href=\"http://www.theskynet.org\"><img src=\"logos/POGS-Reverse.png\" alt=\"POGS\" border=\"0\" height=\"202\" /></a>
        <img src=\"logos/POGSbanner_label.jpg\" alt=\"POGS Banner\" width=\"808\" height=\"202\" border=\"0\" usemap=\"#map\" />
        <map name=\"map\">
            <area shape=\"rect\" coords=\"0,0,200,200\" alt=\"GALEX (Galaxy Evolution Explorer)\" href=\"http://www.galex.caltech.edu\" />
            <area shape=\"rect\" coords=\"203,0,403,200\" alt=\"Pan-STARRS1\" href=\"http://www.ps1sc.org\" />
            <area shape=\"rect\" coords=\"406,0,606,200\" alt=\"WISE (Wide-field Infrared Survey Explorer)\" href=\"http://wise.ssl.berkeley.edu/index.html\" />
            <area shape=\"rect\" coords=\"608,0,808,200\" alt=\"MAGPHYS\" href=\"http://www.iap.fr/magphys/magphys/MAGPHYS.html\" />
        </map>
        <a href=\"http://www.theskynet.org\"><img src=\"logos/theSkyNet-sidebar-Ad-larger-text.gif\" alt=\"theSkyNet POGS\" border=\"0\" height=\"202\" /></a>
   </div>
";

if (!$stopped) {
    get_logged_in_user(false);
    show_login_info();
}

echo "
    <table cellpadding=\"8\" cellspacing=\"4\" class=bordered>
    <tr><td rowspan=\"2\" valign=\"top\" width=\"40%\">
";

if ($stopped) {
    echo "
        <b>".PROJECT." is temporarily shut down for maintenance.
        Please try again later</b>.
    ";
} else {
    db_init();
    show_nav();
}

echo "
    <p>
    <a href=\"http://boinc.berkeley.edu/\"><img align=\"middle\" border=\"0\" src=\"img/pb_boinc.gif\" alt=\"Powered by BOINC\"></a>
    </p>
    <div class=\"fb-like\" data-href=\"http://ec2-23-23-126-96.compute-1.amazonaws.com/pogs\" data-send=\"false\" data-width=\"450\" data-show-faces=\"false\"></div>
    </td>
";

if (!$stopped) {
    $profile = get_current_uotd();
    if ($profile) {
        echo "
            <td class=uotd>
            <h2 class=headline>".tra("User of the day")."</h2>
        ";
        show_uotd($profile);
        echo "</td></tr>\n";
    }
}

echo "
    <tr><td class=news>
    <h2 class=headline>News</h2>
    <p>
";
include("motd.php");
show_news(0, 5);
echo "
    </td>
    </tr></table>
";

page_tail_main();

?>
