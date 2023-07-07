$(document).ready(function () {
    $("#submit").click(function () {
        var top_file = $('#topology').val();
        loadTopology(top_file);
    });
});

function loadTopology(topology_file) {
    console.log(topology_file);
    $.ajax({
        type: "GET",
        url: "makeGraph",
        data: {
            topology: topology_file,
        },
        dataType: "json",
        async: false,
        success: function (response) {
            if(response.success){
                console.log("Graph of the topology is ready");
                window.location.href='graph';
            }else{
                alert("Could not graph the topology");
            }
        }
    });
}