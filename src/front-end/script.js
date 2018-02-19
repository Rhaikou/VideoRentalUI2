"use strict";

// Käytetäänkö lomaketta lisäämiseen vai muokkaamiseen
var mode = 'add';

// Valittun vuokrauksen tiedot
var selected_rent = {
	member: "",
	movie: "",
	rental_date: "",
	return_date: "",
	paid: ""
}

window.onload = function() {
	init_load_indi();
	$( "#login_button" ).on("click", try_login);
}

// Lähettää kirjautumistiedot palvelimelle
function try_login(e) {
	e.preventDefault();
	
	$.ajax({
	asnyc: true,
	url: "/~riherund/cgi-bin/VT5/flask.cgi/kirjaudu",
	type: "POST",
	data: {
		"username": $( "#username" ).val(),
		"password": $( "#password" ).val()
	},
	dataType: "json",
	success: handle_login,
	error: ajax_error
});
}

// Sivun alustus kirjautumisen jälkeen
function init_page() {
	$("#add_button").on("click", submit_form);
	$("#save_button").on("click", save_changes);
	$("#cancel_button").on("click", cancel_changes);
	$("#delete_movie_button").on("click", delete_movie);
	$("#add_movie_button").on("click", add_new_movie);
	$("#link_to_new").on("click", function(e) {
		e.preventDefault();
		window.scrollTo(0,document.body.scrollHeight);
	});
	clear_fields();
	change_mode('add');
	get_rentals();
	get_members();
	get_movies();
	get_genres();
}

// Vaihda lomakkeen tilaa (muokkaus/lisääminen)
function change_mode(mod) {
	if (mod == 'edit') {
		mode = 'edit';
		$("#add_button").attr("disabled", "disabled");
		$("#save_button").removeAttr("disabled");
		$("#cancel_button").removeAttr("disabled");
	}
	else {
		mode = 'add';
		$("#add_button").removeAttr("disabled");
		$("#save_button").attr("disabled", "disabled");
		$("#cancel_button").attr("disabled", "disabled");
	}
}

// Peruu muokkaukset
function cancel_changes(e) {
	if (mode == 'edit') {
		e.preventDefault();
		
		clear_errors();
		clear_fields();
		change_mode('add');
	}
}

// Hakee vuokraukset kannasta
function get_rentals() {
$.ajax({
	async: true,
	url: "/~riherund/cgi-bin/VT5/flask.cgi/hae_vuokraukset",
	type: "GET",
	dataType: "xml",
	success: add_rentals,
	error: ajax_error
});
}

// Hakee jäsenet kannasta
function get_members() {
$.ajax({
	async: true,
	url: "/~riherund/cgi-bin/VT5/flask.cgi/hae_jasenet",
	type: "GET",
	dataType: "json",
	success: add_members,
	error: ajax_error
});
}

// Hakee leffat kannasta
function get_movies() {
$.ajax({
	async: true,
	url: "/~riherund/cgi-bin/VT5/flask.cgi/hae_elokuvat",
	type: "GET",
	dataType: "json",
	success: add_movies,
	error: ajax_error
});
}

// Hakee lajityypit kannasta
function get_genres() {
	$.ajax({
	async: true,
	url: "/~riherund/cgi-bin/VT5/flask.cgi/hae_genret",
	type: "GET",
	dataType: "json",
	success: add_genres,
	error: ajax_error
});
}

// Lähettää uuden vuokrauksen tiedot palvelimelle
function new_rent(member, movie, rental_date, return_date, paid) {
$.ajax({
	asnyc: true,
	url: "/~riherund/cgi-bin/VT5/flask.cgi/lisaa_vuokraus",
	type: "POST",
	data: {
		"member": member,
		"movie": movie,
		"rental_date": rental_date,
		"return_date": return_date,
		"paid": paid
	},
	dataType: "json",
	success: handle_resp,
	error: ajax_error
});
}

// Hakee sivun tiedot palvelimelta
function get_content() {
$.ajax({
	async:true,
	url: "/~riherund/cgi-bin/VT5/flask.cgi/anna_sisalto",
	type: "post",
	dataType: "xml",
	success: handle_content,
	error: ajax_error
});
}

// Laittaa sivun sisällön näkyviin
function handle_content(data, textStatus, request) {
	var div = document.importNode(request.responseXML.documentElement, 1);
	$( "#members_only" ).replaceWith(div);
	init_page();
}

// Käsittelee kirjautumisesta saadun vastauksen
function handle_login(data, textStatus, request) {
	if( data["success"] == 1 ) {
		$( "#login" ).hide();
		get_content();		
	}
	else {
		$( "#err_username" ).text(data["user"]);
		$( "#err_password" ).text(data["pass"]);
		clear_fields();
	}
}

// Käsittelee elokuvan poistosta saadun vastauksen
function handle_delete_movie_resp(data, textStatus, request) {
	$( "#err_movie_delete" ).text(data["msg"]);
	if(data['success'] == 1) {
		get_movies();
		get_rentals();
	}
}

// Käsittelee elokuvan lisäämisestä saadun vastauksen
function handle_add_movie_resp(data, textStatus, request) {
	$( "#err_movie_add" ).text(data["msg"]);
	if (data['success'] == 1) {
		get_movies();
		get_rentals();
		clear_fields();
	}
}

// Käsittelee vuokrauksen lisäämisestä saadun vastauksen
function handle_resp(data, textStatus, request) {
	$( "#err_rental_date" ).text(data["rental_date"]);
	$( "#err_return_date" ).text(data["return_date"]);
	$( "#err_paid" ).text(data["paid"]);
	$( "#err_general" ).text(data["general"]);
	if( data["success"] == 1 ) clear_fields();
	get_rentals();
}

// Käsittelee vuokrauksen muokkauksesta saadun vastauksen
function handle_edit_resp(data, textStatus, request) {
	$( "#err_rental_date" ).text(data["rental_date"]);
	$( "#err_return_date" ).text(data["return_date"]);
	$( "#err_paid" ).text(data["paid"]);
	$( "#err_general" ).text(data["general"]);
	if( data["success"] == 1 ) {
		clear_fields();
		change_mode('add');
	}
	get_rentals();
}

// Käsittelee vuokrauksen klikkaamisen
function handle_click(e) {
	reset_selected();
	if (mode != 'edit') change_mode('edit');
	var row = $(this).text() + "";
	var values = row.split(", ");
	var $li = $(this).parent().parent();
	var movie = $li.find("span").text();
	$( "#members option" ).each( function() {
		if (values[0] == $(this).text()) {
			$(this).attr("selected", "selected");
			return false;
		}
	});
	$( "#movies option" ).each( function() {
		if (movie == $(this).text()) {
			$(this).attr("selected", "selected");
			return false;
		}
	});
	$( "#rental_date" ).val(values[1]);
	if (values[2] == "Palauttamatta") $( "#return_date" ).val("");
	else $( "#return_date" ).val(values[2]);
	$( "#paid" ).val(values[3].replace("€", ""));
	selected_rent.member = $( "#members" ).val();
	selected_rent.movie = $( "#movies" ).val();
	selected_rent.rental_date = values[1];
	selected_rent.return_date = values[2];
	selected_rent.paid = values[3];
	window.scrollTo(0,document.body.scrollHeight);
}

// Lisää palvelimelta saadut vuokraukset sivulle
function add_rentals(data, textStatus, request) {
	var ul = document.importNode(request.responseXML.documentElement, 1);
	$( "#vuokraukset" ).replaceWith(ul);
	$( ".rental_li" ).on("click", handle_click);
}
// Lisää palvelimelta saadut jäsenet alasvetovalikkoon
function add_members(data, textStatus, request) {
	var select = $("<select id=\"members\" name=\"member\"></select");
	for (var i = 0; i < data.length; i++) {
		select.append( $("<option value=\"" + data[i]["id"] + "\">" + data[i]["name"] + "</option>") );
	}
	$( "#members" ).replaceWith(select);
}

// Lisää palvelimelta saadut elokuvat alasvetovalikkoihin
function add_movies(data, textStatus, request) {
	var select1 = $("<select id=\"movies\" name=\"movie\"></select");
	var select2 = $("<select id=\"movies_delete\"></select");
	for (var i = 0; i < data.length; i++) {
		select1.append( $("<option value=\"" + data[i]["id"] + "\">" + data[i]["name"] + " (" + data[i]["year"] + ")</option>") );
		select2.append( $("<option value=\"" + data[i]["id"] + "\">" + data[i]["name"] + " (" + data[i]["year"] + ")</option>") );
	}
	$( "#movies" ).replaceWith(select1);
	$( "#movies_delete" ).replaceWith(select2);
}

// Lisää palvelimelta saadut lajityypit alasvetovalikkoon
function add_genres(data, textStatus, request) {
	var select = $("<select id=\"add_movie_genre\"></select");
	for (var i = 0; i < data.length; i++) {
		select.append( $("<option value=\"" + data[i]["id"] + "\">" + data[i]["name"] + "</option>") );
	}
	$( "#add_movie_genre" ).replaceWith(select);
}

// Lähettää uuden elokuvan tiedot palvelimelle
function add_new_movie(e) {
	e.preventDefault();
	
	clear_errors();
	$.ajax({
	asnyc: true,
	url: "/~riherund/cgi-bin/VT5/flask.cgi/lisaa_elokuva",
	type: "POST",
	data: {
		"name": $("#add_movie_name").val(),
		"year": $("#add_movie_year").val(),
		"price": $("#add_movie_price").val(),
		"review": $("#add_movie_review").val(),
		"genre": $("#add_movie_genre").val()
	},
	dataType: "json",
	success: handle_add_movie_resp,
	error: ajax_error
	});
}

// Lähettää poistettavan elokuvan tiedot palvelimelle
function delete_movie(e) {
	e.preventDefault();
	
	clear_errors();
	$.ajax({
	asnyc: true,
	url: "/~riherund/cgi-bin/VT5/flask.cgi/poista_elokuva",
	type: "POST",
	data: {
		"movie": $("#movies_delete").val()
	},
	dataType: "json",
	success: handle_delete_movie_resp,
	error: ajax_error
});
}

// Käsittelee uuden vuokrauksen lisäämisen
function submit_form(e) {
	e.preventDefault();
	
	clear_errors();
	var member = $( "#members" ).val();
	var movie = $( "#movies" ).val();
	var rental_date = $( "#rental_date" ).val();
	var return_date = $( "#return_date" ).val();
	var paid = $( "#paid" ).val();
	if (mode == 'add') {
		new_rent(member, movie, rental_date, return_date, paid);
	}
}

// Lähettää palvelimelle tiedot vuokrauksen muutoksista
function save_changes(e) {
	e.preventDefault();
	
	clear_errors();
	var member = $( "#members" ).val();
	var movie = $( "#movies" ).val();
	var rental_date = $( "#rental_date" ).val();
	var return_date = $( "#return_date" ).val();
	var paid = $( "#paid" ).val();
	
	$.ajax({
	asnyc: true,
	url: "/~riherund/cgi-bin/VT5/flask.cgi/muokkaa_vuokraus",
	type: "POST",
	data: {
		"member": member,
		"movie": movie,
		"rental_date": rental_date,
		"return_date": return_date,
		"paid": paid,
		"o_member": selected_rent.member,
		"o_movie": selected_rent.movie,
		"o_date": selected_rent.rental_date
	},
	dataType: "json",
	success: handle_edit_resp,
	error: ajax_error
});
}

// Tyhjentää virheilmoitukset
function clear_errors() {
	$( ".err-field" ).text("");
}

// Tyhjentää syöttökentät
function clear_fields() {
	$( "input[type=text]" ).each( function() {
		$(this).val("");
	});
	$( "input[type=password]" ).each( function() {
		$(this).val("");
	});
}

// Poistaa valinnat alasvetovalikoista
function reset_selected() {
	$( "#members option" ).each( function() {
		$(this).removeAttr("selected");
	});
	$( "#movies option" ).each( function() {
		$(this).removeAttr("selected");
	});
}

// Ajaxista tulevat virheet
function ajax_error(xhr, status, error) {
	console.log("Error: " + error );
	console.log("Error: " + error );
	console.log( xhr );
}

// Latausindikaattorin alustus
function init_load_indi() {
	$( document ).ajaxStart(function() {
	$( "#load_indi" ).show();
	});
	$( document ).ajaxStop(function() {
	$( "#load_indi" ).hide();
	});
}
