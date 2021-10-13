angular.module('HanVietDictApp').controller('HanVietDictCtrl', HanVietDictCtrl);
HanVietDictCtrl.$inject = ['$scope', '$http'];

function HanVietDictCtrl($scope, $http)
{
    $scope.test = "Hello World 2";

    $scope.init = function(){

    };
}