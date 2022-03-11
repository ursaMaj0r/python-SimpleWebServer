<?php
exec("ping -c 4 ". $_GET['host'],$output);
print_r( implode($output));
?>