document.addEventListener('DOMContentLoaded', function() {

    var articleContainer = document.querySelector('#a-container');
    var loadingAnimation = document.querySelector('#loading');
    
    var addArticle = function(article, prepend) {
        // Make the article. This is our article template.
        var a = document.createElement('div');
        var hasPic = article.multimedia.length > 0;
        a.className = 'article';
        var s = '';
        if (hasPic) {
            s += '<img class="np" src="http://www.nytimes.com/' + article.multimedia[1].url + '" alt="news">';
        }
        if (article.subsection_name) {
            s += '<p class="meta"><span class="subsection">' + article.subsection_name + '</span></p>';
        }
        s += "<p>" + article.snippet + "</p>";
        a.innerHTML = s;
        
        // Insert the node
        if (!prepend || !articleContainer.firstChild) {
            articleContainer.appendChild(a);
        } else {
            articleContainer.insertBefore(a, articleContainer.firstChild);
        }
    };
    
    var fetchData = function() {
        // Do the usual XHR stuff
        var req = new XMLHttpRequest();
        req.open('GET', '/articles');
        loadingAnimation.classList.remove('hidden');

        req.onload = function() {
            loadingAnimation.classList.add('hidden');
            if (req.status == 200) {
                var dataItems = JSON.parse(req.response);
                for (var i = 0, len = dataItems.length; i < len; i++) {
                    addArticle(dataItems[i]);
                }
            }
            else {
                console.log(req.statusText);
            }
        };
        
        // Handle network errors
        req.onerror = function() {
            loadingAnimation.classList.add('hidden');
            console.log("Network Error");
        };
        
        // Make the request
        req.send();
    };
    
    fetchData();    
});
