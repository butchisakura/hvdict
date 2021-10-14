angular.module('HanVietDictApp').controller('HanVietDictCtrl', HanVietDictCtrl);
HanVietDictCtrl.$inject = ['$scope', '$http'];

function HanVietDictCtrl($scope, $http)
{
    $scope.test = "Hello World 2";

    $scope.init = function(){

    };
}

function render_hanzi(){
    if (!window.HANZI_FIELD)
    {
        return;
    }

    HANZI_FIELD = window.HANZI_FIELD;
    var characters = HANZI_FIELD.split("");
    var js = document.createElement("script");
    for (x of characters) 
    {
        var writer = HanziWriter.create('hanzi-target', x, {
            width: 120,
            height: 120,
            padding: 5,  
            showOutline: true,
            strokeAnimationSpeed: 1,
            delayBetweenStrokes: 150, // milliseconds
            radicalColor: '#dc4e3f' // blue=#337ab7, red=#dc4e3f
        });
        writer.loopCharacterAnimation();
    };
}