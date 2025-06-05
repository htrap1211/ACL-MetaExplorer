<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" indent="yes" encoding="UTF-8"/>
    
    <xsl:template match="/">
        <html>
            <head>
                <title>Academic Paper Metadata Explorer</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                    }
                    .stats {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 20px;
                        margin-bottom: 30px;
                    }
                    .stat-card {
                        background: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    .stat-card h3 {
                        margin: 0;
                        color: #666;
                    }
                    .stat-card p {
                        margin: 10px 0 0;
                        font-size: 24px;
                        font-weight: bold;
                        color: #333;
                    }
                    .filters {
                        background: white;
                        padding: 20px;
                        border-radius: 8px;
                        margin-bottom: 30px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    .filters input, .filters select {
                        padding: 8px;
                        margin: 5px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                    }
                    .papers-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                        gap: 20px;
                    }
                    .paper-card {
                        background: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        transition: transform 0.2s;
                    }
                    .paper-card:hover {
                        transform: translateY(-5px);
                    }
                    .paper-card h3 {
                        margin: 0 0 10px;
                        color: #333;
                    }
                    .paper-card .meta {
                        color: #666;
                        font-size: 0.9em;
                        margin-bottom: 10px;
                    }
                    .paper-card .authors {
                        color: #444;
                        margin-bottom: 10px;
                    }
                    .paper-card .keywords {
                        display: flex;
                        flex-wrap: wrap;
                        gap: 5px;
                    }
                    .paper-card .keyword {
                        background: #e9ecef;
                        padding: 2px 8px;
                        border-radius: 12px;
                        font-size: 0.8em;
                        color: #666;
                    }
                    .paper-card a {
                        display: inline-block;
                        margin-top: 10px;
                        color: #007bff;
                        text-decoration: none;
                    }
                    .paper-card a:hover {
                        text-decoration: underline;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Academic Paper Metadata Explorer</h1>
                    
                    <!-- Statistics Section -->
                    <div class="stats">
                        <div class="stat-card">
                            <h3>Total Papers</h3>
                            <p><xsl:value-of select="count(//paper)"/></p>
                        </div>
                        <div class="stat-card">
                            <h3>Unique Authors</h3>
                            <p><xsl:value-of select="count(//author[not(.=preceding::author)])"/></p>
                        </div>
                        <div class="stat-card">
                            <h3>Years Covered</h3>
                            <p><xsl:value-of select="count(//year[not(.=preceding::year)])"/></p>
                        </div>
                        <div class="stat-card">
                            <h3>Unique Keywords</h3>
                            <p><xsl:value-of select="count(//keyword[not(.=preceding::keyword)])"/></p>
                        </div>
                    </div>
                    
                    <!-- Search and Filter Section -->
                    <div class="filters">
                        <input type="text" id="searchInput" placeholder="Search papers..."/>
                        <select id="yearFilter">
                            <option value="all">All Years</option>
                            <xsl:for-each select="//year[not(.=preceding::year)]">
                                <xsl:sort select="." data-type="number" order="descending"/>
                                <option value="{.}"><xsl:value-of select="."/></option>
                            </xsl:for-each>
                        </select>
                        <select id="keywordFilter">
                            <option value="all">All Keywords</option>
                            <xsl:for-each select="//keyword[not(.=preceding::keyword)]">
                                <xsl:sort select="."/>
                                <option value="{.}"><xsl:value-of select="."/></option>
                            </xsl:for-each>
                        </select>
                    </div>
                    
                    <!-- Papers Grid -->
                    <div class="papers-grid">
                        <xsl:for-each select="//paper">
                            <xsl:sort select="year" data-type="number" order="descending"/>
                            <div class="paper-card">
                                <h3><xsl:value-of select="title"/></h3>
                                <div class="meta">
                                    <xsl:value-of select="year"/> | <xsl:value-of select="venue"/>
                                </div>
                                <div class="authors">
                                    <xsl:for-each select="authors/author">
                                        <xsl:value-of select="."/>
                                        <xsl:if test="position() != last()">, </xsl:if>
                                    </xsl:for-each>
                                </div>
                                <div class="keywords">
                                    <xsl:for-each select="keywords/keyword">
                                        <span class="keyword"><xsl:value-of select="."/></span>
                                    </xsl:for-each>
                                </div>
                                <a href="{url}" target="_blank">View Paper</a>
                            </div>
                        </xsl:for-each>
                    </div>
                </div>
                
                <script>
                    function filterPapers() {
                        const searchTerm = document.getElementById('searchInput').value.toLowerCase();
                        const yearFilter = document.getElementById('yearFilter').value;
                        const keywordFilter = document.getElementById('keywordFilter').value;
                        
                        const papers = document.getElementsByClassName('paper-card');
                        for (let paper of papers) {
                            const title = paper.querySelector('h3').textContent.toLowerCase();
                            const year = paper.querySelector('.meta').textContent.split('|')[0].trim();
                            const keywords = Array.from(paper.querySelectorAll('.keyword'))
                                .map(k => k.textContent.toLowerCase());
                            
                            const matchesSearch = title.includes(searchTerm);
                            const matchesYear = yearFilter === 'all' || year === yearFilter;
                            const matchesKeyword = keywordFilter === 'all' || keywords.includes(keywordFilter.toLowerCase());
                            
                            paper.style.display = matchesSearch &amp;&amp; matchesYear &amp;&amp; matchesKeyword ? 'block' : 'none';
                        }
                    }
                    
                    // Add event listeners
                    document.getElementById('searchInput').addEventListener('input', filterPapers);
                    document.getElementById('yearFilter').addEventListener('change', filterPapers);
                    document.getElementById('keywordFilter').addEventListener('change', filterPapers);
                </script>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet> 