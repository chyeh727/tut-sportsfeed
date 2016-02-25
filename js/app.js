document.addEventListener('DOMContentLoaded', function() {

    var articleContainer = document.querySelector('#a-container');
    var loadingAnimation = document.querySelector('#loading');
    
    var addArticle = function(article, prepend) {
        // Make the article. This is our article template.
        var a = document.createElement('div');
        a.className = 'article';
        var s = '';
        if (article.imgurl) {
            s += '<img class="np" src="http://www.nytimes.com/' + article.imgurl + '" alt="news">';
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
    
    var smallAid = null,
        bigAid = null,
        more = true;
    var fetchingData = false;
    
    var fetchData = function(isUpdate) {
        // We only allow one fetch at a time
        if (fetchingData) {
            return;
        }
        fetchingData = true;
        
        // Do the usual XHR stuff
        var req = new XMLHttpRequest();
        var url = '/articles';
        if (!isUpdate && smallAid !== null) {
            url += '?s=' + smallAid;
        } else if (isUpdate) {
            url += '?b=' + bigAid;
        }
        req.open('GET', url);
        loadingAnimation.classList.remove('hidden');

        req.onload = function() {
            loadingAnimation.classList.add('hidden');
            if (req.status == 200) {
                var resp = JSON.parse(req.response);
                var dataItems = resp.data;
                if (resp.more !== undefined) {
                    more = resp.more;
                }
                
                // Record the date range we have on the view
                if (dataItems.length) {
                    if (bigAid === null || isUpdate) {
                        bigAid = dataItems[0].aid;
                    }
                    if (!isUpdate) {
                        smallAid = dataItems[dataItems.length - 1].aid;
                    }                    
                }
                                
                for (var i = 0, len = dataItems.length; i < len; i++) {
                    addArticle(dataItems[i]);
                }
            }
            else {
                //console.log(req.statusText);
            }
            fetchingData = false;
        };
        
        // Handle network errors
        req.onerror = function() {
            loadingAnimation.classList.add('hidden');
            fetchingData = false;
            //console.log("Network Error");
        };
        
        // Make the request
        req.send();
    };
    
    fetchData();
    
    window.onscroll = function() {
        if (more) {
            var contentHeight = articleContainer.offsetHeight;
            var yOffset = window.pageYOffset;
            var y = yOffset + window.innerHeight;
            if (y >= contentHeight) {
                fetchData();
            }            
        }

    };

});
