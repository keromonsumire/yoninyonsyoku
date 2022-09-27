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

  
  // 確認ボタンをクリックするとイベント発動
  $('#user').click(function() {
  
    // もしキャンセルをクリックしたら
    if (!confirm('本当に削除してよろしいですか？')) {
  
      // submitボタンの効果をキャンセルし、クリックしても何も起きない
      return false;
  
  // 「OK」をクリックした際の処理を記述
    } else {
  
      // HTMLに完了メッセージを表示    
      $('p').text('削除しました');
  
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

  // create_tag.htmlについて
  $(".tag-button1").click(function() {
    $(".bluetags1").toggle();
  });
  $(".tag-button2").click(function() {
    $(".bluetags2").toggle();
  });
  $(".tag-button3").click(function() {
    $(".orangetags1").toggle();
  });
  $(".tag-button4").click(function() {
    $(".orangetags2").toggle();
  });
  $(".tag-button5").click(function() {
    $(".redtags1").toggle();
  });
  $(".tag-button6").click(function() {
    $(".redtags2").toggle();
  });
  $(".tag-button7").click(function() {
    $(".greentags1").toggle();
  });
  $(".tag-button8").click(function() {
    $(".greentags2").toggle();
  });
  $(".tag-button9").click(function() {
    $(".yellowtags1").toggle();
  });
  $(".tag-button10").click(function() {
    $(".yellowtags2").toggle();
  });

  $(".question1").click(function() {
    $(".instance1").toggle();
  });
  
  $(".question2").click(function() {
    $(".instance2").toggle();
  });

  $(".question3").click(function() {
    $(".instance3").toggle();
  });

  $(".question4").click(function() {
    $(".instance4").toggle();
  });

  $(".question5").click(function() {
    $(".instance5").toggle();
  });


});

