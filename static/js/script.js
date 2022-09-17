$(function() {
  // myFormがsubmitされる時
  $('.myForm').submit(function() {
    // text1が入力されていなければ
    if($('.text1').val() == "") {
      // alertを出して
      alert("何か入力してください。");
      // submitを止める
      return false;
    }
    if($('.text2').val() == "") {
      // alertを出して
      alert("何か入力してください。");
      // submitを止める
      return false;
    }
  });

  $("#slider").slick({
    "autoplay":true,
    "autoplayaround":1000
  });

  $(".create-button1").click(function() {
    $(".element2").show();
  });
  $(".create-button2").click(function() {
    $(".element3").show();
  });
  $(".create-button3").click(function() {
    $(".element4").show();
  });
  $(".create-button4").click(function() {
    $(".element5").show();
  });
  $(".create-button5").click(function() {
    $(".element2").hide();
  });
  $(".create-button6").click(function() {
    $(".element3").hide();
  });
  $(".create-button7").click(function() {
    $(".element4").hide();
  });
  $(".create-button8").click(function() {
    $(".element5").hide();
  });

});